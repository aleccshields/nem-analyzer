"""
Regime change detection for FCAS raise/lower spreads.

Flags dispatch intervals where the spread crosses a configurable threshold,
tagging them as compression or expansion events. Produces a timestamped event
log for the DiD model to use when identifying treatment windows.
"""

from typing import Any


def detect_regime_changes(
    spreads: list[dict],
    threshold: float,
) -> list[dict[str, Any]]:
    """
    Identify compression and expansion events in a spread series.

    A compression event is tagged when the spread falls at or below the
    threshold (raise/lower margin narrows — potential battery intervention
    window). An expansion event is tagged when the spread rises back above
    the threshold after being compressed.

    Args:
        spreads: List of spread dicts as produced by raise_lower_spread(),
                 each containing at minimum "interval" and "spread" keys.
        threshold: Spread value (inclusive) at or below which an interval is
                   considered compressed.

    Returns:
        List of event dicts with keys:
            interval    — dispatch interval timestamp string
            spread      — spread value at the event
            event_type  — "compression" | "expansion"
    """
    if not spreads:
        return []

    events: list[dict[str, Any]] = []
    # Track whether the previous interval was in a compressed regime so we
    # can detect the transition back out (expansion).
    prev_compressed = spreads[0]["spread"] <= threshold

    for i, row in enumerate(spreads):
        spread_val = float(row["spread"])
        compressed = spread_val <= threshold

        if i == 0:
            if compressed:
                events.append({
                    "interval": row["interval"],
                    "spread": round(spread_val, 4),
                    "event_type": "compression",
                })
            prev_compressed = compressed
            continue

        if compressed and not prev_compressed:
            events.append({
                "interval": row["interval"],
                "spread": round(spread_val, 4),
                "event_type": "compression",
            })
        elif not compressed and prev_compressed:
            events.append({
                "interval": row["interval"],
                "spread": round(spread_val, 4),
                "event_type": "expansion",
            })

        prev_compressed = compressed

    return events
