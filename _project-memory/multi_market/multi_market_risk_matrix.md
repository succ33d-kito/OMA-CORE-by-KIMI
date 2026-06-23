# OSIRIS Multi-Market Risk Matrix

> Generated: 2026-06-23  
> Purpose: Catalog every known risk class across all target markets with probability, impact, and mitigations.

---

## Risk Taxonomy

| Risk Category | Crypto | Forex | Stocks | Commodities | Indices | Bonds |
|---|---|---|---|---|---|---|
| Market hours | ✅ None | ⚠️ Weekend gap | ⚠️ 6.5h session | ⚠️ Exchange-specific | ❌ Varies | ⚠️ Limited hours |
| Session gaps | ✅ None | ⚠️ Fri 22-Sun 22 | ❌ Night/weekends | ❌ Daily breaks | ❌ Varies | ⚠️ Weekends |
| Spread variation | ✅ Low-fixed | ⚠️ Variable by session | ⚠️ Widens AH | ❌ Widens near expiry | ⚠️ Wide at open | ⚠️ Moderate |
| Liquidity variation | ✅ 24/7 liquid | ✅ Deepest market | ⚠️ Thin AH/PM | ❌ Illiquid near expiry | ⚠️ Varies | ⚠️ Moderate |
| Corporate actions | ✅ None | ✅ None | ❌ Splits/M&A | ⚠️ Futures roll | ⚠️ Rebalance | ⚠️ Maturity |
| Dividends | ✅ None | ✅ None | ❌ Ex-div gaps | ✅ None | ⚠️ ETF dist. | ❌ Coupon |
| Futures rollover | ⚠️ Perpetual | ✅ Spot only | ✅ Spot only | ❌ Critical | ⚠️ Futures | ⚠️ Futures |
| Leverage risk | ❌ Spot only | ❌ 50:1 typical | ⚠️ Margin only | ❌ Varies | ⚠️ Futures | ⚠️ Varies |
| Swap/carry costs | ✅ None | ❌ Daily swap | ✅ None | ⚠️ Contango/bwd | ⚠️ Futures | ❌ Carry |
| Gap risk | ⚠️ Moderate | ⚠️ Weekend | ❌ Earnings gaps | ❌ Inventory rpt | ❌ Overnight | ⚠️ Low |
| Symbol confusion | ⚠️ Minor | ❌ EURUSD=X vs EURUSD | ⚠️ Low | ❌ GC=F vs GOLD | ⚠️ Low | ⚠️ FRED codes |
| Provider consistency | ✅ Binance reliable | ❌ yfinance rate-limited | ❌ yfinance rate-limited | ❌ yfinance rate-limited | ❌ yfinance | ✅ FRED reliable |
| Cross-market correlation | — | ⚠️ USD moves all | ⚠️ Macro-driven | ❌ USD + supply | ⚠️ Tracks SPX | ❌ Inverse stocks |
| Risk model fit | ✅ Validated | ❌ No leverage model | ❌ No earnings model | ❌ No roll model | ❌ No futures | ❌ No duration |

Legend: ✅ = No issue / managed, ⚠️ = Manageable risk, ❌ = Critical gap, — = N/A

---

## 1. Market Hours & Session Gaps

### Risk: Trading a market that is closed
| Market | Hours | Weekend Gap | Highest Risk |
|---|---|---|---|
| Crypto | 24/7 | None | None |
| Forex | Sunday 22:00 UTC — Friday 22:00 UTC | 24h gap (Fri 22 → Sun 22) | Friday positions held over weekend |
| Stocks | M-F 9:30-16:00 ET | 2.5 day gap | Positions held through weekend |
| Commodities | Varies (CME: Sun-Fri with daily break) | ~30h weekend gap | Friday positions, daily close gaps |
| Indices | Varies by index | Weekend gap | Holding index positions |
| Bonds | M-F 6:00-17:00 ET | Weekend gap | Weekend news affecting yields |

**Probability**: High (certain to occur)  
**Impact**: Medium (gap opens against position)  
**Mitigation**: Session-aware trade blocking, widen stops before gaps, reduce size before weekends  
**Required tests**: Session validation rejects off-hours trades

---

## 2. Spread Variation

### Risk: Entry/exit at unfavorable spread
| Market | Normal Spread | Volatile Spread | Peak Spread |
|---|---|---|---|
| Crypto | 0.01-0.05% | 0.1-0.5% | 1%+ (flash crash) |
| Forex (majors) | 0.5-2 pips | 5-20 pips | 50+ pips (event) |
| Stocks (liquid) | 0.01-0.05% | 0.1-0.5% | 1-5% (halt) |
| Commodities | 0.02-0.2% | 0.5-2% | 5%+ (gap) |

**Probability**: Medium (normal regime) / Low (extreme)  
**Impact**: Medium (slippage reduces edge)  
**Mitigation**: Spread-aware position sizing, minimum spread check before entry, avoid illiquid sessions  
**Required tests**: Spread check rejects trades during known wide-spread periods

---

## 3. Liquidity Variation

### Risk: Cannot exit position at fair price

**Probability**: Medium (low for majors, high for exotics/illiquid stocks)  
**Impact**: High (locked position, gap through stop)  
**Mitigation**: Volume-based position limits, minimum volume filter, avoid lowest liquidity hours

### Per-market liquidity profile:
| Market | Deepest Hours | Thinnest Hours | Warning Indicator |
|---|---|---|---|
| Crypto | Always liquid | Brief dips in Asian morning | Volume ratio < 0.5 |
| Forex | London/NY overlap (13:00-17:00 UTC) | Asian session low volatility | Spread > 3x normal |
| Stocks | 9:45-15:30 ET | 9:30-9:45, 15:30-16:00 | Volume < 50% 20d avg |
| Commodities | US morning | Intraday exchange breaks | Open interest decline |

**Required tests**: Liquidity check rejects trades below minimum threshold

---

## 4. Corporate Actions (Stocks)

### Risk: Price discontinuity from non-market events
| Action | Impact | Frequency | Detection Method |
|---|---|---|---|
| Dividend ex-date | Price drops by dividend amount | Quarterly | Calendar-based |
| Stock split | Price adjusts by split ratio | Rare | Corporate action calendar |
| Merger/Acquisition | Price converges to deal price | Rare | News/Event detection |
| Delisting | Price goes to zero | Very rare | Exchange notices |
| Rights offering | Dilution | Rare | Corporate action calendar |

**Probability**: Certain (dividends), Low (others)  
**Impact**: Low (dividends baked into returns), High (delisting)  
**Mitigation**: Dividend calendar for ex-date gaps, exclude stocks with pending M&A  
**Required tests**: Corporate action adjusted OHLCV, dividend gap detection

---

## 5. Futures Rollover (Commodities)

### Risk: Price discontinuity when futures contract expires

| Commodity | Frequency | Roll Period | Typical Gap |
|---|---|---|---|
| Gold (GC) | Quarterly (Feb, Apr, Jun, Aug, Oct, Dec) | ~5 days before expiry | 0.5-2% |
| Crude (CL) | Monthly | ~3 days before expiry | 1-3% |
| Natural Gas (NG) | Monthly | ~3 days before expiry | 2-5% |
| Copper (HG) | Quarterly | ~5 days before expiry | 0.5-1.5% |
| Grains (ZW/ZC/ZS) | Quarterly | ~5 days before expiry | 1-3% |

**Probability**: Certain (100% of positions held through roll)  
**Impact**: High (can cause artificial loss if not adjusted)  
**Mitigation**: Continuous contract construction, roll-adjusted PnL, avoid holding month before expiry  
**Required tests**: Roll-adjusted price series matches raw data within tolerance

---

## 6. Leverage Risk (Forex)

### Risk: Position size amplified by leverage leads to outsized losses

| Constraint | Crypto (Spot) | Forex |
|---|---|---|
| Leverage | 1:1 | 30:1 to 50:1 typical |
| Margin requirement | N/A (full payment) | 2-3% of notional |
| Daily loss 5% of capital | Loses 5% of capital | Can lose 150-250% of capital |
| Position sizing based on | % of capital | Must account for leverage |

**Probability**: High (certain if leverage is used)  
**Impact**: Critical (can exceed account capital)  
**Mitigation**: Apply leverage factor to position size calculation, use notional-based risk limits, separate CapitalGuard for forex with tighter loss limits  
**Required tests**: Leverage-adjusted position sizing, margin call detection

---

## 7. Swap/Overnight Costs (Forex)

### Risk: Daily funding costs erode returns on held positions

| Pair | Typical Swap (per lot per day) | Annualized |
|---|---|---|
| EURUSD | ±$3-8 | ±1-3% |
| GBPUSD | ±$5-12 | ±2-4% |
| USDJPY | ±$4-10 | ±1.5-3.5% |
| AUDUSD | ±$3-6 | ±1-2% |

**Probability**: Certain (every overnight hold)  
**Impact**: Low (individual) / Medium (compounded over many trades)  
**Mitigation**: Include swap in trade PnL, avoid holding through Wednesday (triple swap), prefer pairs with positive carry  
**Required tests**: Swap cost is computed and included in trade PnL

---

## 8. Symbol Mapping Failures

### Risk: Cross-market symbol collisions or provider mismatches

| Conflict Type | Example | Risk Level |
|---|---|---|
| Same instrument, different provider | EURUSD=X vs EURUSD | Medium (partial data) |
| Same ticker, different asset | XRP (crypto) vs hypothetical XRP stock | Low (context disambiguation) |
| Same ticker, different exchange | AAPL (NASDAQ) vs AAPL (other venues) | Low (single exchange focus) |
| Deprecated symbol | Old ticker after rebranding | Low (rare) |
| Provider format mismatch | GC=F vs GOLD vs XAU | Medium (duplicate tracking) |

**Probability**: Medium  
**Impact**: Medium (corrupted data, double-counted positions)  
**Mitigation**: SymbolRegistry as single source of truth, log unmapped symbols, fail on ambiguous resolution  
**Required tests**: SymbolRegistry resolves all known formats, returns None for unknown symbols

---

## 9. Provider Inconsistency

### Risk: Different OHLCV sources give different prices

| Source Pair | Typical Deviation | Worst Case |
|---|---|---|
| Binance vs CoinGecko | <0.1% | 0.5% (low liquidity) |
| yfinance vs direct exchange | 0.1-0.5% | 2% (delayed data) |
| FRED vs other bond data | <0.01% (rates) | 0.1% (revision) |

**Probability**: Medium (yfinance latency is well-known)  
**Impact**: Medium (slippage between signal and execution)  
**Mitigation**: Primary source preference, timestamp comparison, reject stale data  
**Required tests**: Price divergence detection, stale data rejection

---

## 10. Cross-Market Correlation Risk

### Risk: Diversification fails when markets move together

| Correlation Pair | Normal | Crisis (2008) | Crisis (2020) |
|---|---|---|---|
| Crypto ↔ Stocks | 0.3-0.5 | 0.6-0.8 | 0.5-0.7 |
| Forex ↔ Stocks | 0.2-0.4 | 0.5-0.7 | 0.3-0.5 |
| Commodities ↔ Stocks | 0.3-0.5 | 0.6-0.8 | 0.4-0.6 |
| Bonds ↔ Stocks | -0.3 to -0.5 | 0.2-0.4 | -0.1 to 0.2 |

**Probability**: Medium (correlations are regime-dependent)  
**Impact**: High (all portfolios lose simultaneously)  
**Mitigation**: Per-market capital allocation limits, correlation-aware position sizing, increase bond exposure during stress  
**Required tests**: Correlation regime detection, position limit during high-correlation periods

---

## 11. Risk Model Mismatch

### Risk: Using crypto risk model for non-crypto markets

| Risk Parameter | Crypto Value | Appropriate For |
|---|---|---|
| ATR % threshold | 3-8% | Crypto only |
| Daily volatility | 3-6% | Crypto only |
| VaR confidence | 95% | All markets (ok) |
| Max drawdown | 15% (crypto profile) | Tighter for forex (5-10%) |
| Position size | 10% per trade (crypto) | Smaller for forex (2-5%) |
| Daily loss limit | 5% of capital | Tighter for forex (2%) |

**Probability**: High (current code uses crypto values)  
**Impact**: Critical (wrong position sizing for different volatility regimes)  
**Mitigation**: MarketProfile-aware position sizing, per-market CapitalGuard, ATR threshold lookup by market  
**Required tests**: Position sizing uses correct market profile

---

## Risk Score Summary

| # | Risk | Probability | Impact | Risk Score | Priority |
|---|---|---|---|---|---|
| 1 | Market hours / session gaps | High | Medium | **8** | 🔴 Critical |
| 2 | Spread variation | Medium | Medium | **5** | 🟡 High |
| 3 | Liquidity variation | Medium | High | **7** | 🔴 Critical |
| 4 | Corporate actions | Medium | Medium | **5** | 🟡 High |
| 5 | Futures rollover | Certain | High | **10** | 🔴 Critical |
| 6 | Leverage risk | High | Critical | **10** | 🔴 Critical |
| 7 | Swap/overnight costs | Certain | Low | **3** | 🟢 Low |
| 8 | Symbol mapping failures | Medium | Medium | **5** | 🟡 High |
| 9 | Provider inconsistency | Medium | Medium | **4** | 🟡 Medium |
| 10 | Cross-market correlation | Medium | High | **6** | 🔴 Critical |
| 11 | Risk model mismatch | High | Critical | **10** | 🔴 Critical |

Risk Score = Probability × Impact (1-10 scale)

### Priority Action Items

1. **Risk model mismatch** (#11) — Must be fixed before any non-crypto market activation
2. **Leverage risk** (#6) — Must be fixed before forex activation
3. **Futures rollover** (#5) — Must be fixed before commodity activation
4. **Market hours** (#1) — Must be fixed before stock/forex activation
5. **Liquidity** (#3) — Must be addressed for all markets
6. **Cross-market correlation** (#10) — Must be addressed before multi-market portfolio
