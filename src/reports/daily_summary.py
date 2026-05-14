"""
CLI entry point: print a daily spot price summary for a given region and date.

Usage:
    python -m src.reports.daily_summary --region NSW1 --date 2024-01-15
"""

import argparse
import json
import sys
from datetime import date

from src.fetcher.aemo_client import AEMOClient, AEMOClientError
from src.analysis.price_stats import daily_summary, peak_off_peak_split


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Daily NEM spot price summary")
    parser.add_argument("--region", required=True, help="NEM region (e.g. NSW1)")
    parser.add_argument("--date", required=True, help="Settlement date YYYY-MM-DD")
    parser.add_argument("--output", choices=["pretty", "json"], default="pretty")
    return parser.parse_args(argv)


def run(region: str, settlement_date: date, output: str = "pretty") -> int:
    with AEMOClient() as client:
        try:
            prices = client.get_spot_prices(region, settlement_date)
        except (AEMOClientError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    summary = daily_summary(prices)
    split = peak_off_peak_split(prices)

    if output == "json":
        print(json.dumps({"summary": summary, "peak_off_peak": split}, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"  {region}  |  {summary['date']}")
        print(f"{'='*50}")
        print(f"  Intervals:    {summary['n_intervals']}")
        print(f"  Mean RRP:     ${summary['mean']:.2f}/MWh")
        print(f"  Median RRP:   ${summary['median']:.2f}/MWh")
        print(f"  Min / Max:    ${summary['min']:.2f} / ${summary['max']:.2f}")
        print(f"  Std dev:      ${summary['stdev']:.2f}")
        print(f"  Neg periods:  {summary['n_negative']} ({summary['pct_negative']}%)")
        print(f"  Spikes >$300: {summary['n_spike']} ({summary['pct_spike']}%)")
        print(f"\n  Peak (07-22):     mean ${split['peak']['mean']:.2f}  "
              f"[{split['peak']['min']:.2f} - {split['peak']['max']:.2f}]")
        print(f"  Off-peak (22-07): mean ${split['off_peak']['mean']:.2f}  "
              f"[{split['off_peak']['min']:.2f} - {split['off_peak']['max']:.2f}]")
        print()

    return 0


if __name__ == "__main__":
    args = parse_args()
    try:
        settlement_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    sys.exit(run(args.region, settlement_date, args.output))
