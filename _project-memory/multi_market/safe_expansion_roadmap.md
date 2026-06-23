# OSIRIS Multi-Market Safe Expansion Roadmap

> Generated: 2026-06-23  
> Principle: Expand by evidence, not by assumption. Every market must earn activation.

---

## Core Philosophy

```
Research → Backtest → Paper Trading → Live Paper Gate → Demo → Real Capital
```

**No shortcuts.** Each market follows the same progression that crypto validated.

---

## Activation Order

| Rank | Market | Rationale | Risk Score | Confidence |
|---|---|---|---|---|
| **1** | **Forex** | Tightest spreads, most liquid globally, 24/5 schedule, existing OHLCV via yfinance, minimal corporate actions | Low | High |
| **2** | **Stocks** | Largest market cap, strong correlation patterns, existing OHLCV via yfinance, ETF liquidity | Medium | Medium |
| **3** | **Commodities** | Diversification benefit, inflation hedge, but futures complexity adds risk | High | Low |
| **4** | **Indices (via ETFs)** | Already covered by stock symbols (SPY, QQQ, DIA, IWM) — activate alongside stocks | Medium | Medium |
| **5** | **Bonds (via ETFs)** | Lowest priority — FRED data is macro context, not tradeable. Add bond ETFs as stock symbols | Low | Low |

---

## Phase 1: Forex Activation (Estimated: 3-4 sprints)

### Sprint 1: Research Mode (Collect-Only, No Trades)
- [ ] Build Forex OHLCV caching layer (prevent yfinance rate limits)
- [ ] Implement forex session calendar (Sydney, Tokyo, London, NY overlaps)
- [ ] Build forex swap rate tracker
- [ ] Add leverage model to forex market profile
- [ ] Implement central bank event calendar (FOMC, ECB, BOE, BOJ, SNB, RBA, RBNZ, BOC)
- [ ] Write forex data quality tests

**Verification**: All forex events are collected, normalized, and reach Council without crashing. No trades executed.

### Sprint 2: Forex Paper Trading
- [ ] Integrate forex market profile into PaperTradingEngine
- [ ] Build multi-market position sizing (forex ATR thresholds: 0.1-1%)
- [ ] Implement session-aware trade blocking (no entry Friday 21:00 UTC)
- [ ] Build forex weekend gap risk model
- [ ] Add swap cost to trade PnL
- [ ] Implement forex-specific CapitalGuard limits

**Verification**: Forex trades can be paper-executed. PnL accounts for swap costs.

### Sprint 3: Forex Live Paper Gate
- [ ] Build forex historical replay harness (90 days)
- [ ] Run continuous forex paper trading (at least 30 days)
- [ ] Write forex regression tests
- [ ] Pass forex demo gate

**Verification**: 90-day forex paper trading with zero runtime errors, positive PnL, acceptable drawdown.

### Sprint 4: Forex Demo
- [ ] Enable forex in demo mode (real-time paper trading)
- [ ] Monitor 30 days demo
- [ ] Gate decision: GO / CONDITIONAL / NO-GO

---

## Phase 2: Stocks Activation (Estimated: 3-4 sprints)

### Sprint 5: Research Mode
- [ ] Build US market hours calendar (NYSE/NASDAQ)
- [ ] Add global exchange hours and holiday calendar
- [ ] Implement session awareness — block trades outside regular hours
- [ ] Build earnings calendar API integration
- [ ] Implement dividend-aware OHLCV adjustment

**Verification**: Stock events collection and analysis without execution.

### Sprint 6: Paper Trading
- [ ] Integrate stock market profile into PaperTradingEngine
- [ ] Implement earnings gap stop-widening logic
- [ ] Add short-selling restriction checks (hard-to-borrow list)
- [ ] Implement corporate action adjuster
- [ ] Build stock-specific CapitalGuard limits

**Verification**: Stock trades execute in paper mode. Earnings gap risk is modeled.

### Sprint 7: Live Paper Gate
- [ ] Build stock historical replay harness (90 days)
- [ ] Run continuous stock paper trading
- [ ] Write stock regression tests

**Verification**: 90-day stock paper trading.

---

## Phase 3: Commodities Activation (Estimated: 5-6 sprints)

### Sprint 8-9: Research + Futures Infrastructure
- [ ] Build futures rollover / continuous contract logic
- [ ] Implement expiry calendar for all tracked commodities
- [ ] Build contango/backwardation detector
- [ ] Add storage cost and convenience yield model
- [ ] Implement inventory report calendar (EIA, USDA, COMEX)

### Sprint 10-13: Paper Trading + Gate
- [ ] Integrate commodity profile into engine
- [ ] Implement futures-aware position tracking
- [ ] Add commodity-specific risk model
- [ ] Run 90-day commodity paper gate

---

## Phase 4: Indices (ETF Mapping)

### Parallel Track (Sprint 5-7 alongside stocks)
- [ ] Build Index→ETF mapping table: `^GSPC→SPY`, `^IXIC→QQQ`, `^DJI→DIA`, `^RUT→IWM`
- [ ] When stock events reference an index, map to corresponding ETF
- [ ] No separate activation needed — ETFs are traded as stocks

**Effort**: Low (can be completed in 1 sprint alongside stock work)

---

## Phase 5: Bonds (ETF Mapping)

### Parallel Track (lowest priority)
- [ ] Add bond ETF symbols: TLT (long Treasury), IEF (intermediate), SHY (short), BND (total bond)
- [ ] Classify as STOCK for pipeline purposes
- [ ] Keep FRED data as macro context only

**Effort**: Very low (add 4 symbols)

---

## Risk-Scored Readiness Matrix

| Market | Research Ready | Backtest Ready | Paper Ready | Gate Ready | Demo Ready | Capital Ready |
|---|---|---|---|---|---|---|
| **Forex** | ⬜ Sprint 1 | ⬜ Sprint 1-2 | ⬜ Sprint 2-3 | ⬜ Sprint 3 | ⬜ Sprint 4 | ❌ |
| **Stocks** | ⬜ Sprint 5 | ⬜ Sprint 5-6 | ⬜ Sprint 6-7 | ⬜ Sprint 7 | ❌ | ❌ |
| **Commodities** | ⬜ Sprint 8-9 | ⬜ Sprint 9-10 | ⬜ Sprint 10-11 | ❌ | ❌ | ❌ |
| **Indices (ETF)** | ⬜ Sprint 5 | ✅ (trade as SPY) | ✅ (trade as SPY) | ⬜ Sprint 7 | ❌ | ❌ |
| **Bonds (ETF)** | ⬜ Parallel | ❌ | ❌ | ❌ | ❌ | ❌ |

Legend:
- ⬜ = Not started / in progress
- ✅ = Complete
- ❌ = Not available

---

## What Must Not Change (Protected Surface)

The following components are **frozen and protected** by the Crypto Regression Shield (42 tests):

| Component | Protection | Reason |
|---|---|---|
| MarketAgent crypto analysis | ✅ | No change to crypto OHLCV, RSI, ATR, trend logic |
| RiskAgent crypto risk scoring | ✅ | No change to crypto volatility, VaR, correlation |
| AgentCouncil v2 | ✅ | No change to consensus mechanism |
| PaperTradingEngine crypto execution | ✅ | No change to crypto trade flow |
| CapitalGuard guard logic | ✅ | No change to drawdown, loss limits |
| CrashDetector | ✅ | No change to crash velocity detection |
| KnifeDetector | ✅ | No change to knife detection algorithm |
| GapRiskEngine | ✅ | No change to gap risk calculation |
| TradeSignal schema | ✅ | No change to signal structure |
| PerformanceMemory | ✅ | No change to trade recording and attribution |

**All multi-market changes must pass 187 tests (145 existing + 42 crypto regression).**

---

## Guardrails

1. **No activation without gate** — every market must pass a live paper gate before demo
2. **No shared risk limits** — each market gets its own CapitalGuard instance
3. **No cross-market contamination** — a crash in stocks cannot affect crypto positions
4. **Isolated PnL tracking** — performance attribution per market
5. **Sequential activation** — only one market in paper trading at a time until proven stable
