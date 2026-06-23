# OSIRIS Market Enablement Plan

> Generated: 2026-06-23  
> Purpose: Define exactly what is required to activate each asset class for trading.

---

## Phase 0: Universal Foundation (THIS SPRINT)

| Component | Status | Required Before Any Market Activation |
|---|---|---|
| MarketProfile abstraction | ✅ COMPLETE | `core/markets/*.py` — defines trading hours, risk model, constraints per market |
| SymbolRegistry | ✅ COMPLETE | `core/markets/symbol_registry.py` — resolves provider formats to canonical symbols |
| Crypto Regression Shield | ✅ COMPLETE | `tests/test_crypto_regression.py` — 42 tests protecting validated profile |
| Market capability audit | ✅ COMPLETE | This document + `asset_coverage_report.md` + `market_pipeline_trace.md` |

### Remaining universal work (not market-specific):
- [ ] **OHLCV caching layer** — prevent rate-limit failures when all agents request yfinance per cycle
- [ ] **Symbol normalization in event pipeline** — normalize symbols at collection time in WorldMonitorV2 or EventBus

---

## 1. FOREX — Activation Requirements

### Priority: HIGH (lowest risk, most liquid, 24/5)

#### Data Infrastructure
| Requirement | Status | Effort |
|---|---|---|
| Symbol normalization EURUSD=X ↔ EURUSD | ✅ SymbolRegistry handles this | Low |
| Dedicated OHLCV provider for forex | ⚠️ yfinance works but rate-limited | Medium |
| OHLCV caching | ❌ Not implemented | Medium |
| Session calendar (Sydney/Tokyo/London/NY overlaps) | ❌ Not implemented | Medium |

#### Agent Layer
| Requirement | Status | Effort |
|---|---|---|
| MarketAgent forex awareness | ⚠️ Works via yfinance fallback | Low |
| RiskAgent forex-aware risk models | ❌ No leverage, no swap tracking | Medium |
| Add leverage model to risk scoring | ❌ Not implemented | Medium |
| Add central bank event sensitivity | ❌ Not implemented | Medium |

#### Execution Layer
| Requirement | Status | Effort |
|---|---|---|
| Forex market profile integration | ✅ Profile exists — needs binding to PaperTradingEngine | Medium |
| Multi-market position sizing | ❌ ATR-based sizing is crypto-specific | Medium |
| Session-aware trading (no Friday close pos) | ❌ Not implemented | Medium |
| Swap/overnight cost tracking | ❌ Not implemented | Medium |
| Gap risk model for weekend gap | ❌ Not implemented | High |
| Order types for forex (limit vs market) | ⚠️ PaperTrading only — demo needs more | Low |

#### Risk Layer
| Requirement | Status | Effort |
|---|---|---|
| Forex-appropriate ATR thresholds (0.1-1% vs crypto 3-8%) | ❌ Hardcoded crypto values | Low |
| Leverage-based position sizing | ❌ Not implemented | Medium |
| Daily loss in % of account (forex standard: 1-2%) | ⚠️ CapitalGuard supports this, thresholds generic | Low |

#### Validation
| Requirement | Status | Effort |
|---|---|---|
| Forex regression tests | ❌ Not written | Medium |
| Forex paper trading gate | ❌ Not built | High |
| 90-day forex historical backtest | ❌ Not built | High |

### Estimated effort: **3-4 sprints** from start of active development
### Blockers before activation: OHLCV caching, session calendar, swap tracking, position sizing model, gap risk model

---

## 2. STOCKS — Activation Requirements

### Priority: HIGH (largest market cap, high correlation with existing models)

#### Data Infrastructure
| Requirement | Status | Effort |
|---|---|---|
| Stock symbol normalization | ✅ SymbolRegistry handles AAPL, MSFT, etc. | Low |
| Dedicated OHLCV provider | ⚠️ yfinance works but rate-limited | Medium |
| OHLCV caching | ❌ Not implemented | Medium |
| Market hours calendar (US + global) | ❌ Not implemented | High |
| Earnings calendar API | ❌ Not implemented | High |

#### Agent Layer
| Requirement | Status | Effort |
|---|---|---|
| MarketAgent stock analysis | ⚠️ Works via yfinance fallback | Low |
| Earnings gap detection in RiskAgent | ❌ Not implemented | High |
| Dividend-adjusted OHLCV awareness | ❌ Not implemented | Low |

#### Execution Layer
| Requirement | Status | Effort |
|---|---|---|
| Stock market profile integration | ✅ Profile exists — needs binding | Medium |
| Session-aware trading (no 2 AM trades) | ❌ Not implemented | Medium |
| Pre-market / after-hours awareness | ❌ Not implemented | Low |
| Earnings gap stop adjustment | ❌ Not implemented | Medium |
| Dividend/corporate action handling | ❌ Not implemented | Low |
| Short-selling restriction checks | ❌ Not implemented | Medium |

#### Risk Layer
| Requirement | Status | Effort |
|---|---|---|
| Stock-appropriate ATR thresholds (1-3%) | ❌ Hardcoded crypto values | Low |
| Circuit breaker detection | ❌ Not implemented | Medium |
| Exchange-specific risk (halt patterns) | ❌ Not implemented | Medium |

### Estimated effort: **3-4 sprints** from start of active development
### Blockers: Market hours calendar, earnings calendar, earnings gap model, session-aware execution

---

## 3. COMMODITIES — Activation Requirements

### Priority: MEDIUM (higher complexity due to futures)

#### Data Infrastructure
| Requirement | Status | Effort |
|---|---|---|
| Commodity symbol normalization (GC=F ↔ GOLD) | ✅ SymbolRegistry handles this | Low |
| Futures rollover / continuous contract | ❌ Not implemented | High |
| Expiry calendar | ❌ Not implemented | High |
| Storage cost / convenience yield data | ❌ Not implemented | High |

#### Agent Layer
| Requirement | Status | Effort |
|---|---|---|
| MarketAgent commodity analysis | ⚠️ Works via yfinance fallback | Low |
| Contango/backwardation detection | ❌ Not implemented | High |

#### Execution Layer
| Requirement | Status | Effort |
|---|---|---|
| Commodity market profile integration | ✅ Profile exists — needs binding | Medium |
| Futures rollover in position tracking | ❌ Not implemented | High |
| Contract month awareness | ❌ Not implemented | High |

#### Risk Layer
| Requirement | Status | Effort |
|---|---|---|
| Commodity ATR thresholds (1-5% varies widely) | ❌ Hardcoded crypto values | Low |
| Inventory report event calendar | ❌ Not implemented | High |

### Estimated effort: **5-6 sprints** from start of active development
### Blockers: Futures rollover logic, continuous contract construction, expiry calendar

---

## 4. INDICES — Activation Requirements

### Priority: LOW (cannot be traded directly)

#### Fundamental Issue
Indices (^GSPC, ^IXIC, etc.) are **not directly tradeable instruments**. To trade an index, OSIRIS would need to:
1. Trade index futures (/ES for S&P 500, /NQ for NASDAQ, etc.)
2. Trade index ETFs (SPY, QQQ, etc.) — already tracked as STOCKS
3. Use CFDs (not currently supported)

#### Recommended Approach
**Do not trade indices directly.** Instead:
- `^GSPC` → trade `SPY` ETF (already in stock symbol list)
- `^IXIC` → trade `QQQ` ETF (already in stock symbol list)
- `^DJI` → trade `DIA` ETF (already in stock symbol list)
- `^RUT` → trade `IWM` ETF (already in stock symbol list)

### Activation Requirements (if trading index futures)
| Requirement | Effort |
|---|---|
| Index futures rollover model | High |
| Futures margin model | High |
| Index-to-ETF mapping table | Low |
| Futures-specific risk (gap limit up/down) | High |

### Estimated effort: **2 sprints** (for ETF mapping path, 5+ for futures)

---

## 5. BONDS — Activation Requirements

### Priority: LOWEST (no tradeable instrument in current pipeline)

#### Fundamental Issue
FRED data provides **yield series, not prices**:
- `DGS10` = 10-year Treasury yield (%) — no OHLCV
- `DGS2` = 2-year Treasury yield (%) — no OHLCV
- `T10Y2Y` = yield spread — no OHLCV
- `DFF` = Fed Funds rate — no OHLCV

To trade bonds, OSIRIS would need:
1. Bond ETF prices (TLT for long-duration, SHY for short-duration, etc.)
2. Bond futures (ZB, ZN, etc.)
3. A yield-to-price conversion model

#### Recommended Approach
**Do not trade bonds via FRED data.** If bond exposure is desired:
- Add bond ETF tickers (TLT, IEF, SHY, BND) to stock symbol list
- Treat bond ETFs as stocks for pipeline purposes
- Keep FRED data for macro context only

### Activation Requirements (if pursuing bond ETFs)
| Requirement | Effort |
|---|---|
| Add bond ETF symbols to stock list | Low |
| Duration-based risk model | Medium |
| Yield curve awareness (inversion detection) | Low (macro agent can handle) |

---

## Activation Priority Ranking

| Rank | Market | Risk | Reward | Complexity | Recommendation |
|---|---|---|---|---|---|
| 1 | **Forex** | Low | High (tight spreads, liquid) | Medium | **Activate first** |
| 2 | **Stocks** | Medium | High (largest market) | Medium | Activate second |
| 3 | **Commodities** | High | Medium | High | Activate third |
| 4 | **Indices** | Medium | High (via ETFs) | Low | Activate via ETF mapping |
| 5 | **Bonds** | Low | Low (via ETFs) | Low | Activate last via ETFs |

---

## Recommended Sprint Schedule

| Sprint | Focus | Deliverables |
|---|---|---|
| Current | Universal Foundation | MarketProfile, SymbolRegistry, audit reports, tests |
| 1 | Forex research mode | Session calendar, swap tracker, leverage model, OHLCV cache |
| 2 | Forex Paper Trading | Forex market profile in engine, position sizing, gap risk model |
| 3 | Forever Live Paper Gate | 90-day forex historical replay, forex regression tests |
| 4 | Stocks research mode | Market hours calendar, earnings API, session-blocking |
| 5 | Stocks Paper Trading | Stock market profile in engine, earnings gap adjustment |
| 6 | Stocks Live Paper Gate | 90-day stock historical replay, stock regression tests |
| 7-8 | Commodities (futures work) | Futures rollover, continuous contract, expiry calendar |
| 9 | Indices (ETF mapping) | Index-to-ETF mapping, activate SPY/QQQ/DIA/IWM |
| 10 | Bond ETFs | Add TLT/IEF/SHY/BND, duration risk model |
