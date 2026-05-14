# nem-analyzer

NEM spot price and FCAS spread analyzer that pulls live data from the AEMO API and generates daily market summaries for use in battery storage research.

## Stack

- Python 3.12
- pytest for tests, ruff for linting
- AEMO NEMWEB API (unauthenticated, public)
- python-dotenv for environment config
- Key libraries: requests, pandas, numpy (see requirements.txt for pinned versions)

## Commands

- Run all tests: `pytest tests/ -v`
- Run single test file: `pytest tests/test_fcas_spreads.py -v`
- Lint: `ruff check . --fix`
- Daily summary report: `python -m src.reports.daily_summary`

## Structure

- `src/fetcher/` — AEMO API client; all external HTTP calls live here
- `src/analysis/price_stats.py` — spot price statistics: daily summary, peak/off-peak splits
- `src/analysis/fcas_spreads.py` — raise/lower spread calculations (core thesis logic)
- `src/reports/daily_summary.py` — CLI entry point; orchestrates fetch → analysis → output
- `tests/` — mirrors src/ structure; all tests currently passing

## Conventions

- All AEMO data fetching goes through `aemo_client.py` — never call the API directly from analysis modules
- Analysis functions are pure: no I/O, no side effects, take DataFrames in and return DataFrames/dicts out
- snake_case everywhere, including column names in DataFrames
- Tests must cover any new analysis function before it's used in reports
- Region codes follow AEMO convention: NSW1, VIC1, QLD1, SA1, TAS1

## Constraints

- Do not add new dependencies without flagging first — the AEMO data pipeline has strict reproducibility requirements for the thesis
- Never hardcode dispatch interval timestamps; always derive from fetched data
- `.env` holds API base URL and timeout config — use `.env.example` as reference, never commit `.env`
- FCAS market types: raise (R6S, R60S, R5MI, RREG) and lower (L6S, L60S, L5MI, LREG) — do not conflate them

## Current work

- Building panel dataset of FCAS prices across all five NEM regions using NEMOSIS and NemPriceSetter XML data
- Difference-in-differences methodology for battery storage thesis — analysis scaffolding lives in `src/analysis/fcas_spreads.py`
- Data engineering for panel construction is in progress — do not refactor `fcas_spreads.py` until DiD spec is finalized
- Adding a regime change detector in `src/analysis/regime_detector.py` — flags dispatch intervals where FCAS raise/lower spreads cross a configurable threshold, tagging them as potential "battery intervention" events; produces a timestamped event log that the DiD model can use to identify treatment windows programmatically rather than by hand
