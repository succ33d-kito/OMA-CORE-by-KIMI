# OSIRIS Crypto Regression Gate Report

> Generated: 2026-06-23

---

## Test Suite Results

| Test File | Status |
|---|---|
| `tests/test_crypto_regression.py` | ✅ PASS (42/42) |
| `tests/test_integration.py` | ✅ PASS |
| `tests/test_survival_replay.py` | ✅ PASS |
| `tests/test_crash_detector_v2.py` | ✅ PASS |
| `tests/test_kill_switch.py` | ✅ PASS |
| `tests/test_knife_detector.py` | ✅ PASS |
| `tests/test_market_agent.py` | ✅ PASS |
| `tests/test_risk_agent.py` | ✅ PASS |
| `tests/test_council_v2.py` | ✅ PASS |
| `tests/test_trade_schema.py` | ✅ PASS |
| All other test files | ✅ PASS |

**Total: 187 passed, 0 failed, 3 warnings**

---

## Guarded Test Files

| File | Tests | Purpose |
|---|---|---|
| `test_crypto_regression.py` | 42 | Crypto profile regression shield |
| `test_integration.py` | — | Full pipeline integration |
| `test_survival_replay.py` | 8 | Crash/guard/kill-switch historical replay |
| `test_crash_detector_v2.py` | — | Crash detector correctness |
| `test_kill_switch.py` | — | Kill switch behavior |
| `test_knife_detector.py` | — | Knife detector correctness |
| `test_market_agent.py` | — | Market agent analysis |
| `test_risk_agent.py` | — | Risk agent analysis |
| `test_council_v2.py` | — | Council v2 decision-making |
| `test_trade_schema.py` | 8 | Trade signal and trade serialization |

---

## Verdict

**NO REGRESSIONS.** Crypto Trading Profile v1 remains frozen and validated.

All 187 tests pass with zero changes to any protected component.

```
python -m pytest tests/ -v --tb=no
187 passed in 43.86s
```

---

## Protected Components Confirmed Unchanged

| Component | Status |
|---|---|
| `core/agents/market_agent.py` | ✅ Unchanged |
| `core/agents/risk_agent.py` | ✅ Unchanged |
| `core/council/council.py` | ✅ Unchanged |
| `core/execution/paper_trading.py` | ✅ Unchanged |
| `core/execution/capital_guard.py` | ✅ Unchanged |
| `core/execution/crash_detector.py` | ✅ Unchanged |
| `core/execution/knife_detector.py` | ✅ Unchanged |
| `core/execution/gap_risk.py` | ✅ Unchanged |
| `core/execution/direction_controller.py` | ✅ Unchanged |
| `core/execution/slippage.py` | ✅ Unchanged |
| `core/execution/performance_memory.py` | ✅ Unchanged |
| `core/schemas/trade_schema.py` | ✅ Unchanged |
| `core/schemas/agent_schema.py` | ✅ Unchanged |
| `core/markets/symbol_registry.py` | ✅ Unchanged |
| `tests/test_crypto_regression.py` | ✅ Unchanged |
