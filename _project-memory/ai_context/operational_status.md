# Operational Status

## Current Status

| Component | Status |
|-----------|--------|
| **Smoke Run** | 🟢 **RUNNING** — cycle 3/672, started 2026-06-23 22:27 UTC |
| **Tests** | 🟢 277 passed, 4 skipped (network-dependent), 0 failed |
| **Micro Capital** | 🔴 NO-GO |
| **Real Capital** | 🔴 NO-GO |
| **Forex** | 🔴 NO-GO |
| **Operational Validation** | 🟢 COMPLETE |

## Smoke Run Details

| Metric | Value |
|--------|-------|
| Cycles completed | 3 |
| Events processed | 6 |
| Signals generated | 0 |
| Trades opened | 0 |
| Guard blocks | 6 |
| Runtime errors | 0 |
| Data failures | 0 |
| Guard mode | normal |
| Crash mode | none |
| Equity | 10,000.00 |

## Audit Findings (from operational validation sprint)

| Area | Finding | Status |
|------|---------|--------|
| **Test reconciliation** | 281 total tests (277 pass + 4 skip). 269/12 was obsolete baseline. | ✅ RESOLVED |
| **Architecture map** | Full pipeline + all modules + output files documented | ✅ COMPLETE |
| **Execution blocks** | 11 records (old session). 100% `execution_capacity_limit`. Counters match (11=11). | ✅ ALL EXPLAINED |
| **Guard blocks** | 6 records (current smoke run). All have `guard_source: "Unknown"`, `block_reason: "unknown"`. | ❌ FLAW-25 |
| **Health status** | 10 checks. All currently HEALTHY. All trigger conditions documented. | ✅ COMPLETE |
| **FLAW-24** | Non-blocking. Trade safety unaffected. Fix planned after smoke run. | 🔶 OPEN |
| **FLAW-21** | Low risk. Defense-in-depth fix before Micro Capital. | 🔶 OPEN |
| **Preflight** | 20/20 checks → GO_FOR_7D_SMOKE | ✅ COMPLETE |

## Health Monitor (Last Cycle)

| Check | Status |
|-------|--------|
| process_alive | ✅ HEALTHY |
| equity_sanity | ✅ HEALTHY |
| capital_guard_mode | ✅ HEALTHY (normal) |
| crash_mode | ✅ HEALTHY (none) |
| open_positions | ✅ HEALTHY (0 open) |
| position_sizes | ✅ HEALTHY |
| trade_consistency | ✅ HEALTHY |
| price_data | ✅ HEALTHY |
| cycle_diversity | ✅ HEALTHY |
| excessive_skips | ✅ HEALTHY |

## Security Status

| Check | Status |
|-------|--------|
| Real capital mode | ✅ DISABLED (OSIRIS_REAL_CAPITAL=false) |
| Binance API keys | ✅ Not present in environment |
| .gitignore for JSONL | ✅ Configured |
| .gitignore for logs | ✅ Configured |
