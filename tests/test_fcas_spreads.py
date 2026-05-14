"""Tests for src/analysis/fcas_spreads.py"""

import pytest
from src.analysis.fcas_spreads import raise_lower_spread, spread_summary


def make_fcas(interval: str, rrp: float, fcas_type: str, region: str = "NSW1") -> dict:
    return {
        "interval": interval,
        "region": region,
        "fcas_type": fcas_type,
        "rrp": rrp,
        "availability": 50.0,
    }


RAISE = [
    make_fcas("2024-01-15T00:05:00", 10.0, "RAISE6SEC"),
    make_fcas("2024-01-15T00:10:00", 15.0, "RAISE6SEC"),
    make_fcas("2024-01-15T00:15:00", 5.0,  "RAISE6SEC"),
]
LOWER = [
    make_fcas("2024-01-15T00:05:00", 8.0,  "LOWER6SEC"),
    make_fcas("2024-01-15T00:10:00", 20.0, "LOWER6SEC"),  # lower > raise: neg spread
    make_fcas("2024-01-15T00:15:00", 3.0,  "LOWER6SEC"),
]


class TestRaiseLowerSpread:
    def test_spread_calculation(self):
        spreads = raise_lower_spread(RAISE, LOWER, "6SEC")
        assert spreads[0]["spread"] == pytest.approx(2.0)   # 10 - 8
        assert spreads[1]["spread"] == pytest.approx(-5.0)  # 15 - 20
        assert spreads[2]["spread"] == pytest.approx(2.0)   # 5 - 3

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            raise_lower_spread(RAISE, LOWER[:2], "6SEC")

    def test_interval_mismatch_raises(self):
        bad_lower = list(LOWER)
        bad_lower[1] = make_fcas("2024-01-15T99:99:00", 20.0, "LOWER6SEC")
        with pytest.raises(ValueError, match="Interval mismatch"):
            raise_lower_spread(RAISE, bad_lower, "6SEC")


class TestSpreadSummary:
    def setup_method(self):
        spreads = raise_lower_spread(RAISE, LOWER, "6SEC")
        self.summary = spread_summary(spreads)

    def test_n_intervals(self):
        assert self.summary["n_intervals"] == 3

    def test_median_spread(self):
        assert self.summary["median_spread"] == pytest.approx(2.0)

    def test_pct_negative(self):
        assert self.summary["pct_negative_spread"] == pytest.approx(33.3, rel=0.01)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            spread_summary([])
