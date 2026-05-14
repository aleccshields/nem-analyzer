"""Tests for src/analysis/price_stats.py"""

import pytest
from src.analysis.price_stats import (
    validate_prices,
    extract_rrps,
    daily_summary,
    peak_off_peak_split,
)


def make_price(interval: str, rrp: float, region: str = "NSW1") -> dict:
    return {"interval": interval, "region": region, "rrp": rrp, "totaldemand": 7000.0}


SAMPLE_PRICES = [
    make_price("2024-01-15T00:05:00", 45.20),
    make_price("2024-01-15T00:10:00", 51.10),
    make_price("2024-01-15T08:00:00", 120.50),
    make_price("2024-01-15T14:30:00", 450.00),  # spike
    make_price("2024-01-15T23:00:00", -80.00),  # negative
]


class TestValidatePrices:
    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_prices([])

    def test_missing_key_raises(self):
        bad = [{"interval": "2024-01-15T00:05:00", "region": "NSW1"}]  # missing rrp
        with pytest.raises(ValueError, match="missing keys"):
            validate_prices(bad)

    def test_valid_passes(self):
        validate_prices(SAMPLE_PRICES)  # should not raise


class TestExtractRrps:
    def test_returns_floats(self):
        rrps = extract_rrps(SAMPLE_PRICES)
        assert all(isinstance(r, float) for r in rrps)

    def test_correct_values(self):
        rrps = extract_rrps(SAMPLE_PRICES)
        assert rrps == [45.20, 51.10, 120.50, 450.00, -80.00]


class TestDailySummary:
    def setup_method(self):
        self.summary = daily_summary(SAMPLE_PRICES)

    def test_region(self):
        assert self.summary["region"] == "NSW1"

    def test_n_intervals(self):
        assert self.summary["n_intervals"] == 5

    def test_negative_count(self):
        assert self.summary["n_negative"] == 1
        assert self.summary["pct_negative"] == 20.0

    def test_spike_count(self):
        assert self.summary["n_spike"] == 1
        assert self.summary["pct_spike"] == 20.0

    def test_min_max(self):
        assert self.summary["min"] == -80.00
        assert self.summary["max"] == 450.00

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            daily_summary([])


class TestPeakOffPeakSplit:
    def test_peak_includes_08_and_14(self):
        result = peak_off_peak_split(SAMPLE_PRICES)
        # 08:00 (120.50) and 14:30 (450.00) should be peak
        assert result["peak"]["n"] == 2
        assert result["peak"]["max"] == 450.00

    def test_off_peak_includes_midnight_and_23(self):
        result = peak_off_peak_split(SAMPLE_PRICES)
        # 00:05, 00:10, 23:00 should be off-peak
        assert result["off_peak"]["n"] == 3
        assert result["off_peak"]["min"] == -80.00


class TestMixedRegions:
    def test_validate_prices_raises_on_mixed_regions(self):
        prices = [
            make_price("2024-01-15T00:05:00", 45.00, region="NSW1"),
            make_price("2024-01-15T00:10:00", 51.00, region="VIC1"),
        ]
        with pytest.raises(ValueError, match="region"):
            validate_prices(prices)

    def test_daily_summary_raises_on_mixed_regions(self):
        prices = [
            make_price("2024-01-15T00:05:00", 45.00, region="NSW1"),
            make_price("2024-01-15T00:10:00", 51.00, region="VIC1"),
        ]
        with pytest.raises(ValueError, match="region"):
            daily_summary(prices)


class TestMixedDates:
    def test_validate_prices_raises_on_mixed_dates(self):
        prices = [
            make_price("2024-01-15T23:55:00", 45.00),
            make_price("2024-01-16T00:05:00", 51.00),
        ]
        with pytest.raises(ValueError, match="date"):
            validate_prices(prices)

    def test_daily_summary_raises_on_mixed_dates(self):
        prices = [
            make_price("2024-01-15T23:55:00", 45.00),
            make_price("2024-01-16T00:05:00", 51.00),
        ]
        with pytest.raises(ValueError, match="date"):
            daily_summary(prices)
