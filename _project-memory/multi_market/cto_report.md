# OSIRIS Multi-Market Sprint — CTO Report

> Date: 2026-06-23  
> Author: OSIRIS Engineering  
> Subject: Multi-Market Foundation Sprint — Final Assessment

---

## Q1: Is OSIRIS currently multi-market?

**No.** OSIRIS is a **crypto trading engine** that **collects** multi-market data but **trades** only crypto.

Current state:
| Activity | Scope |
|---|---|
| Collects | 115 symbols across 6 asset classes (crypto, forex, stocks, commodities, indices, bonds) |
| Analyzes | Any asset class with OHLCV data (crypto via Binance, rest via yfinance fallback) |
| Councils | Any asset class that passes ScoreEngine (crypto passes, bonds/indices may not) |
| Trades | Crypto ONLY (15 Binance spot pairs) |

**Verdict**: OSIRIS has **multi-market awareness** but **crypto-only execution**.

---

## Q2: What percentage of the architecture is already market-agnostic?

Breakdown by architectural layer:

| Layer | Market-Agnostic? | Evidence |
|---|---|---|
| **Data Collection** | ✅ **100%** | 7 collectors covering 6 asset classes. No crypto-specific bias in collection. |
| **Event Schema** | ✅ **100%** | `AssetClass` enum, `Asset` dataclass with symbol/class/exchange. Fully generic. |
| **EventBus** | ✅ **100%** | Pure pub-sub. No market awareness. |
| **ScoreEngine** | ⚠️ **Partial** | `_calculate_asset_relevance()` has crypto bias (70 for crypto vs 50 for others). Otherwise generic. |
| **MarketAgent** | ⚠️ **Partial** | Binance OHLCV native for crypto, yfinance fallback works for others. Analysis is technical (RSI, ATR, trend) — market-agnostic. |
| **RiskAgent** | ⚠️ **Partial** | Same OHLCV fallback pattern. Crypto-specific risk thresholds. Otherwise generic. |
| **NewsAgent** | ✅ **100%** | Market-agnostic by design (processes news text). |
| **MacroAgent** | ✅ **100%** | Processes macro data regardless of market. |
| **TrendAgent** | ✅ **100%** | Trend analysis on any time series. |
| **AgentCouncil v2** | ✅ **100%** | Generic consensus mechanism. No market awareness. |
| **PaperTradingEngine** | ❌ **Crypto-only** | Hardcoded BTC gap risk tracking, crypto ATR position sizing, no market profile integration. |
| **CapitalGuard** | ❌ **Crypto-only** | Crypto-specific drawdown thresholds, loss limits. No per-market configuration. |
| **CrashDetector** | ❌ **Crypto-only** | Hardcoded 24/7 operating assumption. Cannot handle session gaps. |
| **KnifeDetector** | ❌ **Crypto-only** | Same 24/7 assumption. |
| **GapRiskEngine** | ❌ **Crypto-only** | Only tracks BTC price. No concept of weekend gap. |
| **DirectionController** | ⚠️ **Partial** | Generic WR tracking. Could work for any market. |

**Overall**: ~60% market-agnostic. The **execution and risk layers** are crypto-specific and must be made multi-market before any non-crypto activation.

---

## Q3: What prevents Forex activation?

### Primary Blockers (must fix before any forex trade)

| Blocker | Location | Details |
|---|---|---|
| **No forex market profile in execution** | PaperTradingEngine | Engine has no concept of forex sessions, spreads, leverage, or position sizing |
| **No leverage model** | RiskAgent + PaperTradingEngine | Forex uses 30:1-50:1 leverage. Current position sizing assumes 1:1. |
| **No session calendar** | PaperTradingEngine | Would trade forex at Friday 23:00 UTC (market closed) |
| **No swap cost tracking** | PaperTradingEngine | PnL would be incorrect for overnight holds |
| **No weekend gap risk** | GapRiskEngine | BTC-only gap tracking. Forex gaps Friday→Sunday are fundamentally different. |
| **Missing OHLCV caching** | All agents | yfinance rate-limits cause failures when all agents request OHLCV per event cycle |

### Secondary Blockers (should fix before activation)

| Blocker | Details |
|---|---|
| Symbol normalization (EURUSD=X vs EURUSD) | ✅ Mitigated by SymbolRegistry |
| Forex-specific ATR thresholds | Crypto ATR (3-8%) incorrect for forex (0.1-1%) |
| Central bank event calendar | FOMC/ECB/BOE events cause major volatility |
| Forex-specific regression tests | No test coverage for forex execution |

### Total effort: 3-4 sprints

---

## Q4: What prevents Stocks activation?

### Primary Blockers

| Blocker | Location | Details |
|---|---|---|
| **No market hours calendar** | PaperTradingEngine | Would trade AAPL at 2:00 AM Saturday |
| **No earnings gap risk** | PaperTradingEngine + RiskAgent | Cannot widen stops before earnings, no earnings calendar |
| **No market profile in execution** | PaperTradingEngine | Same fundamental issue as forex |
| **No session-aware blocking** | Execution layer | No pre-market/after-hours/distinction |

### Secondary Blockers

| Blocker | Details |
|---|---|
| No dividend adjustment in OHLCV | Price history needs adjustment for ex-dividend drops |
| No corporate action handling | Splits, mergers, delistings unhandled |
| No short-selling restriction check | Cannot detect hard-to-borrow stocks |
| Missing OHLCV caching | Same yfinance rate-limit issue |
| Stock-specific risk thresholds | ATR 1-3% vs crypto 3-8% |

### Total effort: 3-4 sprints

---

## Q5: What prevents Commodities activation?

### Primary Blockers

| Blocker | Location | Details |
|---|---|---|
| **No futures rollover logic** | Data + Execution | GC=F price jumps at contract expiry. Continuous contract requires roll adjustment. |
| **No expiry calendar** | Data layer | Cannot know when current contract expires |
| **No contango/backwardation model** | RiskAgent | Cannot detect when rolling costs are unfavorable |
| **No storage cost model** | RiskAgent | Convenience yield affects futures pricing |
| **No inventory event calendar** | RiskAgent | EIA (oil), USDA (grains), COMEX (metals) reports cause major gaps |

### Secondary Blockers

| Blocker | Details |
|---|---|
| Symbol normalization (GC=F vs GOLD) | ✅ Mitigated by SymbolRegistry |
| Different market hours per commodity | CME metals vs NYMEX energy vs CBOT grains |
| Commodity-specific ATR | Oil 2-5%, Gold 0.5-1.5%, Grains 1-3% |
| Physical delivery mechanics | Not relevant for paper but must understand |
| Missing OHLCV caching | Same yfinance rate-limit issue |

### Total effort: 5-6 sprints

---

## Q6: What can be activated next with lowest risk?

### Recommendation: **Forex** (in order)

**Rationale for Forex first:**
1. **Tightest spreads** of any market (0.5-2 pips for majors)
2. **Deepest liquidity** ($7.5T/day — largest market globally)
3. **24/5 schedule** — no daily open gap like stocks (only weekend gap)
4. **No corporate actions** — no dividends, splits, or earnings
5. **Existing OHLCV** via yfinance (works now, needs caching)
6. **SymbolRegistry handles forex** — EURUSD=X ↔ EURUSD resolution is implemented
7. **Most similar risk profile** to crypto (continuous trading, technical analysis works)

**Why not stocks first:** Stocks have a harder session gap (6.5h/day vs forex 24/5), earnings gaps require calendar integration, dividends need adjustment. The session model alone is more complex than forex.

### Alternative: ETFs as stocks (SPY, QQQ, DIA, IWM)

These are already collected and analyzed. They could be activated with less incremental work than forex because:
- Already trade like stocks in the pipeline
- Already have OHLCV via yfinance
- No leverage or swap concerns

**Risk**: Without stock market hours model, ETFs would trade at 2 AM Saturday.

### Verdict: Forex is the lowest-risk next activation, but ETFs (SPY/QQQ) could be activated first with a simpler hours model.

---

## Q7: What must never be changed because it protects the validated crypto profile?

### Frozen Components (Crypto Trading Profile v1)

| Component | Protection | Why Frozen |
|---|---|---|
| **Crypto OHLCV pipeline** | MarketAgent `_fetch_ohlcv` for Binance symbols | Any change could alter crypto trade signals |
| **Crypto technical analysis** | RSI, ATR, SMA calculations in MarketAgent | Crypto-specific thresholds validated by 90-day gate |
| **Crypto risk scoring** | RiskAgent volatility, VaR for crypto | Crypto-specific vol regime (3-8%) |
| **Council consensus mechanism** | AgentCouncil v2 | Mechanism is market-agnostic but adjustments could impact crypto decision quality |
| **PaperTradingEngine crypto flow** | Signal creation, position sizing, stop/target logic | Validated by 90-day gate with 81 trades |
| **CapitalGuard crypto thresholds** | Drawdown limits, mode transitions | Kept system alive through 3.92% max drawdown |
| **CrashDetector crypto logic** | BTC-specific price velocity thresholds | Successfully detected in historical replays (COVID, FTX, LUNA) |
| **GapRiskEngine** | BTC price tracking | Validated gap risk detection |
| **TradeSignal/Trade schemas** | All trade data structures | No change to schema required for multi-market |
| **PerformanceMemory** | Trade recording and attribution | Market-agnostic, no change needed |
| **Crypto Regression Shield** | 42 tests in `tests/test_crypto_regression.py` | Must pass 100% before any release |

### What CAN be safely extended

| Component | Extension Strategy |
|---|---|
| `core/markets/` | ✅ NEW — built this sprint. No crypto code touched. |
| `core/markets/symbol_registry.py` | ✅ NEW — symbol resolution only. No crypto execution logic. |
| PaperTradingEngine | **Add market profile lookup** — factory pattern, existing crypto flow untouched |
| CapitalGuard | **Market-specific instances** — separate guard per market, crypto guard frozen |
| GapRiskEngine | **Multi-symbol support** — add forex/stock tracking alongside BTC |
| CrashDetector | **Per-market crash detector** — different thresholds per market, crypto frozen |
| ScoreEngine | **Remove crypto bias** — make relevance scoring market-agnostic (base 70 for all) |

### Golden Rule

> **If a change touches any line of code that was validated by the 90-day live paper gate, it must pass all 187 tests before being considered safe.**

---

## Appendix: Sprint Deliverables Checklist

| Deliverable | Status | Location |
|---|---|---|
| `core/markets/__init__.py` | ✅ COMPLETE | `core/markets/__init__.py` |
| `core/markets/base.py` | ✅ COMPLETE | `core/markets/base.py` |
| `core/markets/crypto.py` | ✅ COMPLETE | `core/markets/crypto.py` |
| `core/markets/forex.py` | ✅ COMPLETE | `core/markets/forex.py` |
| `core/markets/stocks.py` | ✅ COMPLETE | `core/markets/stocks.py` |
| `core/markets/commodities.py` | ✅ COMPLETE | `core/markets/commodities.py` |
| `core/markets/bonds.py` | ✅ COMPLETE | `core/markets/bonds.py` |
| `core/markets/indices.py` | ✅ COMPLETE | `core/markets/indices.py` |
| `core/markets/symbol_registry.py` | ✅ COMPLETE | `core/markets/symbol_registry.py` |
| `asset_coverage_report.md` | ✅ COMPLETE | `_project-memory/multi_market/asset_coverage_report.md` |
| `market_pipeline_trace.md` | ✅ COMPLETE | `_project-memory/multi_market/market_pipeline_trace.md` |
| `market_enablement_plan.md` | ✅ COMPLETE | `_project-memory/multi_market/market_enablement_plan.md` |
| `safe_expansion_roadmap.md` | ✅ COMPLETE | `_project-memory/multi_market/safe_expansion_roadmap.md` |
| `multi_market_risk_matrix.md` | ✅ COMPLETE | `_project-memory/multi_market/multi_market_risk_matrix.md` |
| Crypto Regression Shield | ✅ PASSED | 187 tests passing |
| No crypto modifications | ✅ VERIFIED | Zero lines of crypto execution code changed |
