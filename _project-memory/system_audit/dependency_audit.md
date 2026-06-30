# Dependency Audit

## requirements.txt

```text
requests>=2.31.0
feedparser>=6.0.10
yfinance>=0.2.28
pandas>=2.0.0
numpy>=1.24.0
rich>=13.0.0
tabulate>=0.9.0
yfinance
feedparser
python-dotenv
python-dotenv
flask
python-binance
gunicorn>=21.0.0
psycopg2-binary>=2.9.0

```

## pip check

```text
No broken requirements found.
```

## Duplicate requirements

['feedparser', 'yfinance', 'python-dotenv']

## Installed security tooling status

- `pip_audit`: not installed
- `safety`: not installed
- `bandit`: not installed
- `coverage`: not installed

## Dependency risks

- `requirements.txt` contains duplicate entries for `yfinance`, `feedparser`, and `python-dotenv`.
- Several dependencies are unpinned (`yfinance`, `feedparser`, `python-dotenv`, `flask`, `python-binance`). This creates reproducibility and supply-chain risk.
- `psycopg2-binary` exists but SQLite remains primary in code paths; Postgres maturity unclear.
- Network-facing packages (`requests`, `yfinance`, `feedparser`, `python-binance`) require timeout, retry, rate-limit, and source-governance discipline.

## Maintenance verdict

Dependencies are manageable but not production-hardened. Pinning, lockfiles, vulnerability scanning, and dependency ownership are needed before production.
