"""
AEMO public data client.

Pulls 5-minute dispatch price and FCAS availability data from the
AEMO NEMWeb public archive. No authentication required.
"""

import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AEMO_BASE_URL", "https://visualisationtools.market.aemo.com.au")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))

VALID_REGIONS = {"NSW1", "QLD1", "SA1", "TAS1", "VIC1"}
VALID_FCAS_TYPES = {"RAISE6SEC", "RAISE60SEC", "RAISE5MIN", "RAISEREG",
                    "LOWER6SEC", "LOWER60SEC", "LOWER5MIN", "LOWERREG"}


class AEMOClientError(Exception):
    pass


class AEMOClient:
    """Thin wrapper around the AEMO public visualisation API."""

    def __init__(self, base_url: str = BASE_URL, timeout: int = TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_spot_prices(self, region: str, settlement_date: date) -> list[dict]:
        """
        Return 5-minute dispatch prices for a region on a given day.

        Args:
            region: NEM region ID (e.g. "NSW1", "VIC1")
            settlement_date: The trading day to retrieve

        Returns:
            List of dicts with keys: interval, region, rrp, totaldemand

        Raises:
            AEMOClientError: on network failure or unexpected response
            ValueError: on invalid region
        """
        if region not in VALID_REGIONS:
            raise ValueError(f"Invalid region '{region}'. Must be one of {VALID_REGIONS}")

        url = f"{self.base_url}/api/spot-prices"
        params = {
            "region": region,
            "settlementdate": settlement_date.isoformat(),
        }

        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            raise AEMOClientError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise AEMOClientError(f"HTTP {e.response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise AEMOClientError(f"Network error: {e}")

        data = resp.json()
        if "prices" not in data:
            raise AEMOClientError(f"Unexpected response shape: {list(data.keys())}")

        return data["prices"]

    def get_fcas_prices(self, fcas_type: str, settlement_date: date) -> list[dict]:
        """
        Return FCAS clearing prices across all regions for a given day and service type.

        Args:
            fcas_type: Service type string (e.g. "RAISE6SEC", "LOWERREG")
            settlement_date: The trading day to retrieve

        Returns:
            List of dicts with keys: interval, region, fcas_type, rrp, availability

        Raises:
            AEMOClientError: on network or response errors
            ValueError: on invalid fcas_type
        """
        if fcas_type not in VALID_FCAS_TYPES:
            raise ValueError(f"Invalid FCAS type '{fcas_type}'. Must be one of {VALID_FCAS_TYPES}")

        url = f"{self.base_url}/api/fcas-prices"
        params = {
            "fcastype": fcas_type,
            "settlementdate": settlement_date.isoformat(),
        }

        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            raise AEMOClientError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise AEMOClientError(f"HTTP {e.response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise AEMOClientError(f"Network error: {e}")

        data = resp.json()
        if "fcas" not in data:
            raise AEMOClientError(f"Unexpected response shape: {list(data.keys())}")

        return data["fcas"]

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
