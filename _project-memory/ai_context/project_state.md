# OSIRIS / O.M.A.-C.O.R.E. — Project State

Generated: 2026-06-23 23:00 UTC

## Overview

| Field | Value |
|-------|-------|
| **Project Name** | O.M.A.-C.O.R.E. (One Man Army — Cosmic OSIRIS Intelligence Engine) |
| **Version** | 2.1.0 |
| **Vision** | From global events to intelligent action — a multi-profile decision engine that observes, evaluates, and executes across Trader, Entrepreneur, and Creator personas. |
| **Current Phase** | Extended Demo — 7-Day Smoke Run |
| **Current Milestone** | Operational Validation Consolidation |
| **Current Status** | Smoke Run ACTIVE (3 cycles completed) |
| **Smoke Run Started** | 2026-06-23 22:27 UTC |
| **Test Status** | 277 passed, 4 skipped (network-dependent), 0 failed |

## Repository State

| Field | Value |
|-------|-------|
| **Latest Commit** | `0135683` — "Add operational validation audits and smoke-run preflight" |
| **Current Branch** | `main` |
| **All Tests** | `python -m pytest tests/ -q` → 277 passed, 4 skipped, 0 failed |
| **Crypto Regression** | 42 tests — all pass |
| **Survival Replay** | 11 tests — all pass |

## Current Constraints

- **DO NOT** modify MarketAgent, RiskAgent, AgentCouncil, PaperTradingEngine, CapitalGuard, CrashDetector, KnifeDetector, GapRiskEngine, DirectionController, SlippageEngine, PerformanceMemory
- **DO NOT** modify trading logic, signal logic, risk logic, execution logic, portfolio logic
- **DO NOT** create new agents, indicators, collectors, dashboards, databases, or broker integrations
- **DO NOT** optimize for PnL, return, or Sharpe
- **Allowed:** monitoring, telemetry, reporting scripts, audit scripts, tests, documentation, .gitignore

## Capital Status

| Stage | Status |
|-------|--------|
| Micro Capital | 🚫 NO-GO |
| Real Capital | 🚫 NO-GO |
| Forex Activation | 🚫 NO-GO |

## Current Priority

1. **7-Day Smoke Run** — ACTIVE
2. FLAW-25 Guard Audit Attribution
3. FLAW-24 CrashDetector Reporting Equity
4. FLAW-21 Trade.close() Idempotency

## Current Next Step

Monitor the active 7-day smoke run. If it completes without NO-GO triggers:
→ Generate daily reports via `scripts/extended_demo_report.py`
→ Evaluate gate criteria
→ Proceed to 30-day validation run
