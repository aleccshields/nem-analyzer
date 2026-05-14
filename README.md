# NEM Analyzer

A Python toolkit for pulling and analyzing electricity spot prices and FCAS market data
from Australia's National Electricity Market (NEM).

Fetches data from the AEMO public API, computes region-level statistics, and produces
simple summary reports. Intended as a lightweight research utility — not production-grade.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env
pytest tests/ -v
python -m src.reports.daily_summary --region NSW1 --date 2024-01-15
```

## Structure

- `src/fetcher/`  — AEMO API client and data retrieval
- `src/analysis/` — price statistics, FCAS spread calculations
- `src/reports/`  — report generation and CLI entry points
- `tests/`        — mirrors src/ structure
- `data/`         — local cache (not committed)
