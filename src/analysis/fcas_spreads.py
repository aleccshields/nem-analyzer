"""
FCAS spread and volatility calculations.

Used to analyse how battery storage entry affects FCAS clearing prices —
particularly the raise/lower spread compression thesis.
"""

from statistics import mean, median, stdev
from typing import Any


def raise_lower_spread(
    raise_prices: list[dict],
    lower_prices: list[dict],
    fcas_service: str,
) -> list[dict[str, Any]]:
    """
    Compute interval-level raise/lower spreads for matched contingency services.

    Args:
        raise_prices: Raw FCAS dicts for the raise service (e.g. RAISE6SEC)
        lower_prices: Raw FCAS dicts for the corresponding lower service
        fcas_service: Base service name for labelling (e.g. "6SEC")

    Returns:
        List of dicts: interval, raise_rrp, lower_rrp, spread
    """
    if len(raise_prices) != len(lower_prices):
        raise ValueError(
            f"Raise ({len(raise_prices)}) and lower ({len(lower_prices)}) "
            "price lists must have the same length"
        )

    results = []
    for r, lo in zip(raise_prices, lower_prices):
        if r["interval"] != lo["interval"]:
            raise ValueError(
                f"Interval mismatch: raise={r['interval']} lower={lo['interval']}"
            )
        raise_rrp = float(r["rrp"])
        lower_rrp = float(lo["rrp"])
        results.append({
            "interval": r["interval"],
            "service": fcas_service,
            "raise_rrp": raise_rrp,
            "lower_rrp": lower_rrp,
            "spread": round(raise_rrp - lower_rrp, 4),
        })
    return results


def spread_summary(spreads: list[dict]) -> dict[str, Any]:
    """
    Aggregate spread statistics across a day or period.
    """
    if not spreads:
        raise ValueError("Spread list is empty")

    vals = [s["spread"] for s in spreads]
    return {
        "service": spreads[0]["service"],
        "n_intervals": len(vals),
        "mean_spread": round(mean(vals), 4),
        "median_spread": round(median(vals), 4),
        "stdev_spread": round(stdev(vals) if len(vals) > 1 else 0.0, 4),
        "min_spread": round(min(vals), 4),
        "max_spread": round(max(vals), 4),
        "pct_negative_spread": round(100 * sum(1 for v in vals if v < 0) / len(vals), 1),
    }
