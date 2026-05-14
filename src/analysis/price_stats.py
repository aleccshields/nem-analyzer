"""
Spot price statistics for a single region-day.

All functions accept a list of raw price dicts as returned by AEMOClient.get_spot_prices()
and return plain Python scalars or dicts — no pandas required for the core logic.
"""

from datetime import datetime
from statistics import mean, median, stdev
from typing import Any

# NEM spot prices are capped at these values (AUD/MWh)
PRICE_FLOOR = -1000.0
MARKET_PRICE_CAP = 16600.0

# Threshold used in our spike detection heuristic
SPIKE_THRESHOLD = 300.0


def validate_prices(prices: list[dict]) -> None:
    """Raise ValueError if the price list looks malformed."""
    if not prices:
        raise ValueError("Price list is empty")
    required_keys = {"interval", "region", "rrp"}
    expected_region = prices[0]["region"]
    expected_date = prices[0]["interval"][:10]
    for i, row in enumerate(prices):
        missing = required_keys - set(row.keys())
        if missing:
            raise ValueError(f"Row {i} missing keys: {missing}")
        if row["region"] != expected_region:
            raise ValueError(
                f"Row {i} has region '{row['region']}'; expected '{expected_region}'"
            )
        if row["interval"][:10] != expected_date:
            raise ValueError(
                f"Row {i} has date '{row['interval'][:10]}'; expected '{expected_date}'"
            )


def extract_rrps(prices: list[dict]) -> list[float]:
    """Pull the RRP values out of raw price dicts."""
    return [float(row["rrp"]) for row in prices]


def daily_summary(prices: list[dict]) -> dict[str, Any]:
    """
    Compute a standard set of daily price statistics.

    Returns:
        Dict with keys: region, date, n_intervals, mean, median, min, max,
        stdev, n_negative, n_spike, pct_negative, pct_spike
    """
    validate_prices(prices)
    rrps = extract_rrps(prices)
    n = len(rrps)

    n_negative = sum(1 for r in rrps if r < 0)
    n_spike = sum(1 for r in rrps if r > SPIKE_THRESHOLD)

    return {
        "region": prices[0]["region"],
        "date": datetime.fromisoformat(prices[0]["interval"]).date().isoformat(),
        "n_intervals": n,
        "mean": round(mean(rrps), 2),
        "median": round(median(rrps), 2),
        "min": round(min(rrps), 2),
        "max": round(max(rrps), 2),
        "stdev": round(stdev(rrps) if n > 1 else 0.0, 2),
        "n_negative": n_negative,
        "n_spike": n_spike,
        "pct_negative": round(100 * n_negative / n, 1),
        "pct_spike": round(100 * n_spike / n, 1),
    }


def peak_off_peak_split(prices: list[dict]) -> dict[str, dict]:
    """
    Split prices into peak (07:00-22:00) and off-peak buckets and
    return summary stats for each.

    NEM intervals are labelled by their *end* time.
    """
    validate_prices(prices)

    peak, off_peak = [], []
    for row in prices:
        hour = datetime.fromisoformat(row["interval"]).hour
        bucket = peak if 7 <= hour < 22 else off_peak
        bucket.append(float(row["rrp"]))

    def stats(rrps: list[float]) -> dict:
        if not rrps:
            return {"n": 0, "mean": None, "min": None, "max": None}
        return {
            "n": len(rrps),
            "mean": round(mean(rrps), 2),
            "min": round(min(rrps), 2),
            "max": round(max(rrps), 2),
        }

    return {"peak": stats(peak), "off_peak": stats(off_peak)}
