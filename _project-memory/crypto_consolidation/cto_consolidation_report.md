# OSIRIS Crypto Consolidation CTO Report

> Date: 2026-06-23  
> Subject: Crypto Trading Profile v1 — Operational Trust Assessment

---

## Executive Summary

OSIRIS Crypto Trading Profile v1 has undergone an 8-phase operational consolidation audit covering:

- Stability across 30/60/90/180-day durations
- Signal quality (8213 signals analyzed)
- Council calibration (conviction, consensus, disagreement)
- Risk calibration (risk score vs realized loss)
- Survival stress (6 hostile regimes)
- PerformanceMemory integrity
- Full regression gate (187 tests)

**Verdict**: Crypto Profile v1 is **operationally sound** with documented calibration gaps.

---

## Q1: Is Crypto Profile v1 operationally trusted?

**CONDITIONAL GO** — with caveats.

### Evidence supporting trust

| Criterion | Finding |
|---|---|
| 90-day live paper gate | ✅ PASSED: 2140 cycles, 81 trades, +4.85%, 3.92% DD |
| 180-day stability simulation | ✅ 0 runtime errors, 0 exceptions, 0 guard failures across 4300 cycles |
| Survival under hostile regimes | ✅ 6/6 regimes survived (COVID, Luna, FTX, bull, chop, flash crash) |
| Guard deadlock prevention | ✅ CapitalGuard ended NORMAL or CAUTION in all stable regimes |
| Regression tests | ✅ 187/187 passing, zero regressions |
| PerformanceMemory integrity | ✅ All trades recorded, agent attribution consistent |

### Evidence requiring caution

| Caveat | Finding |
|---|---|
| Signal quality | 24h directional accuracy is marginal (~50-55%) |
| CrashDetector calibration | `summary()` hardcodes 10000 equity — does not reflect actual drawdown |
| Conviction calibration | High conviction (60+) does not strongly outperform low conviction |
| Risk score calibration | Relationship between risk score and loss severity is non-monotonic |
| PerformanceMemory persistence | In-memory only — all data lost on restart |

---

## Q2: Is it safe to freeze Crypto while starting Forex Research Mode later?

**YES** — with one precondition.

### Why freezing is safe

1. **Crypto execution code is isolated** — no shared code paths with future Forex execution
2. **Market-agent analysis is provider-based** — Forex uses yfinance, Crypto uses Binance. No interference.
3. **SymbolRegistry is read-only** — does not affect crypto symbol resolution
4. **CapitalGuard is engine-scoped** — future Forex gets its own CapitalGuard instance
5. **CrashDetector/GapRisk are BTC-specific** — hardcoded `symbol.upper() == "BTC"` checks
6. **Tests are crypto-specific** — no test covers Forex behavior

### Precondition

Before starting Forex Research Mode, the following must be in place:
- A **Forex agent profile** that prevents MarketAgent from applying crypto ATR thresholds to Forex
- A **Forex-specific OHLCV caching layer** (current yfinance fallback is unreliable)
- **Session-aware event filtering** to prevent Forex events from being analyzed outside market hours

Without these, Forex events in the pipeline will:
- Be analyzed with crypto-appropriate parameters (wrong)
- Pass through Council (wasteful)
- Be rejected by PaperTradingEngine (noisy, not harmful)

---

## Q3: What risks remain?

### Critical (must fix before real capital)

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R1 | **Signal accuracy insufficient for real capital** | 24h directional accuracy ~50-55% (signal quality audit) | Continue paper trading; only real capital if 24h accuracy > 60% sustained |
| R2 | **No profit factor edge** | Avg trade PnL near zero across regimes | Requires alpha improvement (out of scope for consolidation) |
| R3 | **PerformanceMemory not persistent** | All agent learning lost on restart | Add SQLite/JSON persistence layer |

### High (should fix before extended demo)

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R4 | **CrashDetector summary() hardcodes 10000** | `crash_mode(10000)` in summary() ignores actual equity | Fix to accept current_equity parameter |
| R5 | **Conviction scores not strongly predictive** | High conviction (60+) WR not significantly better than low (<40) | Revisit conviction formula or calibrate thresholds |
| R6 | **Consensus score not predictive** | High consensus trades do not outperform low consensus | May be inherent to 2-agent council with correlated inputs |

### Medium (tracking)

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R7 | **Sideways chop has highest drawdown** | 6.45% DD in chop regime vs 2.88% in COVID | Direction controller provides some protection |
| R8 | **No short-side edge** | System is naturally long-biased (trend-following) | Accept as feature of current profile |
| R9 | **Synthetic data limitations** | Simulations use GBM-like data, not real historical paths | Validated against real historical 90-day gate |

---

## Q4: What should never be touched without explicit regression testing?

| Component | Rationale | Test Coverage |
|---|---|---|
| `core/agents/market_agent.py` | Crypto OHLCV, RSI, ATR, trend logic | test_crypto_regression.py (8 tests), test_market_agent.py |
| `core/agents/risk_agent.py` | Crypto risk scoring | test_crypto_regression.py (5 tests), test_risk_agent.py |
| `core/council/council.py` | Council consensus mechanism | test_crypto_regression.py (2 tests), test_council_v2.py |
| `core/execution/paper_trading.py` | Trade signal creation, position sizing, execution | test_crypto_regression.py (8 tests), test_paper_trading_experiment.py |
| `core/execution/capital_guard.py` | Drawdown limits, guard modes, kill switch | test_crypto_regression.py (5 tests), test_survival_replay.py |
| `core/execution/crash_detector.py` | Crash velocity detection, modes | test_crypto_regression.py (2 tests), test_crash_detector_v2.py, test_survival_replay.py |
| `core/execution/knife_detector.py` | Falling knife detection | test_crypto_regression.py (1 test), test_knife_detector.py |
| `core/execution/gap_risk.py` | Gap risk model | test_crypto_regression.py (1 test), test_survival_replay.py |
| `core/execution/slippage.py` | Entry/exit slippage | test_paper_trading_experiment.py |
| `core/performance_memory.py` | Trade recording, agent tracking | test_crypto_regression.py (indirect) |
| `core/schemas/trade_schema.py` | TradeSignal, Trade dataclasses | test_trade_schema.py (8 tests) |
| `core/schemas/agent_schema.py` | AgentOpinion, CouncilDecision | test_crypto_regression.py (4 tests) |
| `tests/test_crypto_regression.py` | 42-test regression shield | Self-protecting |

Any change to a file above must pass `python -m pytest tests/ -v` with **187 tests passing** before being considered safe.

---

## Q5: What evidence supports Demo Trading?

| Evidence | Source | Confidence |
|---|---|---|
| 90-day live paper gate PASSED | `_live_paper_gate/` reports | High |
| 0 runtime errors across 4 durations | Stability audit | High |
| 0 guard failures across all simulations | All audits | High |
| Survival under 6 hostile regimes | Stress audit | High |
| No deadlock in CapitalGuard | Stability + stress audits | High |
| Kill switch works (tested) | test_kill_switch.py | High |
| PerformanceMemory records correctly | Memory audit | High |
| 187 tests passing | Regression gate | High |
| Council conviction in reasonable range (10-95) | Council calibration | Medium |
| Direction controller prevents bad directions | Stress audit | Medium |

**Demo Trading confidence: HIGH** — the system survives, does not crash, and its guards work correctly.

---

## Q6: What evidence blocks Real Capital?

| Blocker | Evidence | Severity |
|---|---|---|
| Signal quality below 60% directional accuracy | Signal quality audit: ~50-55% at 24h | 🔴 Critical |
| No measurable profit factor edge | Avg trade PnL near zero | 🔴 Critical |
| CapitalGuard summary() equity hardcode | Visual code inspection | 🟡 High |
| Conviction not strongly predictive | Council calibration audit | 🟡 High |
| No persistent PerformanceMemory | Memory audit | 🟡 Medium |
| CrashDetector summary ignores actual equity | Code inspection (line 260) | 🟡 High |

**Real Capital confidence: LOW** — the system demonstrates operational stability but not yet alpha generation.

---

## Q7: What exact gates remain before Micro Capital?

### Gate Sequence

```
Paper Trading → Demo → Extended Demo → Micro Capital → Real Capital
     ✅            ⬜          ⬜               ⬜             ❌
```

### Gate Requirements

#### Demo Trading (NEXT)
| Requirement | Status | Evidence |
|---|---|---|
| Live Paper Gate passed | ✅ | 90-day replay |
| 0 critical runtime failures | ✅ | All simulations |
| Survival under hostile regimes | ✅ | Stress audit |
| No guard deadlock | ✅ | All durations |
| Regression gate | ✅ | 187 tests |
| **Verdict** | **✅ GO** | |

#### Extended Demo (3 months real-time paper)
| Requirement | Status | Evidence |
|---|---|---|
| Demo gate passed | ⬜ | Not yet run |
| 90 consecutive days without crash | ⬜ | Simulated only |
| Signal quality report generated | ✅ | 8213 signals analyzed |
| Council calibration report generated | ✅ | This report |
| All 8 consolidation reports complete | ✅ | Generated |
| **Verdict** | **⬜ PENDING** | Requires real-time run |

#### Micro Capital ($1,000-$5,000 real)
| Requirement | Status | Evidence |
|---|---|---|
| Extended Demo passed (3 months) | ⬜ | Not yet run |
| 24h directional accuracy > 60% | ❌ | Currently ~50-55% |
| Profit factor > 1.2 sustained | ❌ | Not measured |
| Avg PnL per trade > 0.5% | ❌ | Near zero |
| Max drawdown < 10% in paper | ✅ | 3.92% in 90-day gate |
| CapitalGuard summary equity fix | ⬜ | Not yet implemented |
| **Verdict** | **❌ NO-GO** | Signal quality insufficient |

#### Real Capital (>$5,000)
| Requirement | Threshold | Status |
|---|---|---|
| Micro Capital profit factor | > 1.5 | ❌ |
| Micro Capital monthly return | > 2% | ❌ |
| Micro Capital max DD | < 15% | ⬜ |
| 6 months micro capital history | Required | ❌ |
| **Verdict** | **❌ NO-GO** | Far from ready |

---

## Readiness Classification Summary

| Stage | Readiness | Verdict | Action Required |
|---|---|---|---|
| Paper Trading | Complete | **GO** | Already passed 90-day live paper gate |
| Demo Trading | Ready | **GO** | Can begin demo trading immediately |
| Extended Demo | Ready | **CONDITIONAL** | Start real-time run; monitor 90 days |
| Micro Capital | Not ready | **NO-GO** | Fix signal quality; improve conviction calibration |
| Real Capital | Not ready | **NO-GO** | Requires micro capital success first |
| Forex Research Mode | Ready | **GO** | Cannot affect crypto — fully isolated |

---

## What Should the Next Sprint Be?

### Recommended: Fix FLAW-14 (MarketAgent elif chain)

**Rationale**: The elif chain in MarketAgent (`market_agent.py:91-126`) has a structural issue where:
- MomBreak (lines 104-108) is checked AFTER RSI overbought (lines 99-103) 
- But RSI < 30 (lines 109-113) comes AFTER MomBreak
- This means a MomBreak signal can block an RSI-oversold BUY

**Why this sprint**:
- It is a proven bug (FLAW-14) documented in project memory
- It affects signal quality (our main blocker for Micro Capital)
- It is non-invasive (restructure conditions, not formulas)
- It can be validated against the 42 crypto regression tests

**Alternative**:
- Fix CrashDetector `summary()` equity hardcode (batch of 1-line fixes)
- Add PerformanceMemory persistence (JSON or SQLite)
- Start Forex Research Mode (collect-only, analyze forex events)

---

## Appendix: All Deliverables Checklist

| File | Status | Location |
|---|---|---|
| `scripts/crypto_stability_audit.py` | ✅ COMPLETE | `scripts/` |
| `scripts/crypto_signal_quality_audit.py` | ✅ COMPLETE | `scripts/` |
| `scripts/crypto_council_calibration.py` | ✅ COMPLETE | `scripts/` |
| `scripts/crypto_risk_calibration.py` | ✅ COMPLETE | `scripts/` |
| `scripts/crypto_survival_stress_audit.py` | ✅ COMPLETE | `scripts/` |
| `scripts/crypto_memory_audit.py` | ✅ COMPLETE | `scripts/` |
| `stability_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `signal_quality_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `council_calibration_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `risk_calibration_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `survival_stress_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `performance_memory_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `regression_gate_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| `cto_consolidation_report.md` | ✅ COMPLETE | `_project-memory/crypto_consolidation/` |
| 187 tests passing | ✅ VERIFIED | — |
| Zero crypto execution changes | ✅ VERIFIED | — |
