# Trading Audit

## Scope

Audited without modifying trading logic.

## Components

| Component | Evidence | Strengths | Weaknesses / unknowns | Status |
|---|---|---|---|---|
| MarketAgent | `core/agents/market_agent.py`, tests | Generates market-oriented signal reasoning | Needs live-source robustness and calibration proof | Experimental |
| RiskAgent | `core/agents/risk_agent.py`, tests | Explicit risk reasoning exists | Not proven as mandatory gate for every execution path | Partial |
| Council | `core/council/*`, tests | Aggregation model exists | Not proven under adversarial/multi-agent conflict | Partial |
| Execution | `core/execution/*` and `core/execution_engine/*` | Rich legacy experiments plus certified new domain | Duplicated execution worlds; integration unclear | Critical risk |
| CapitalGuard | `core/execution/capital_guard.py` | Guard concept exists | Enforcement across all paths unproven | Partial |
| CrashDetector | `core/execution/crash_detector.py` | Defensive detection exists | False-positive/false-negative performance unknown | Partial |
| KnifeDetector | `core/execution/knife_detector.py` | Falling-knife protection concept exists | Market regime robustness unknown | Partial |
| GapRisk | `core/execution/gap_risk.py` | Gap risk concept exists | Coverage by market/session unknown | Partial |
| DirectionController | `core/execution/direction_controller.py` | Directional controls exist | Interaction with council/execution not fully certified | Partial |
| PerformanceMemory | `core/execution/performance_memory.py` | Learning/feedback memory exists | File growth and bias risks | Experimental |

## Strengths

- Many important trading safety concepts are represented.
- Tests exist for several trading modules.
- Governance has begun separating operational facts from scientific knowledge.

## Open flaws / unknown behavior

- No production broker/exchange readiness.
- No certified unified order path from council through risk into execution.
- No proven kill-switch hierarchy for all paths.
- No market-regime validation or live slippage proof.
- No production capital allocation authority model.

## Verdict

Trading subsystem is research-grade and internally useful, but not production/live trading ready.
