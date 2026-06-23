# OSIRIS Market Pipeline Trace

> Generated: 2026-06-23  
> Purpose: Trace every asset class through the entire OSIRIS pipeline to identify exact blocking points.

---

## Pipeline Architecture

```
WorldMonitorV2
  → EventBus (EventTopic.EVENTS_RAW)
    → ScoreEngine (relevance filtering)
      → Agent Swarm (analysis + opinion)
        → AgentCouncil v2 (consensus)
          → PaperTradingEngine (execution)
            → CapitalGuard / CrashDetector / KnifeDetector / GapRisk
```

---

## CRYPTO — FULL FLOW

### Data Collection
- **Sources**: BinanceCollector (15 pairs), CoinGeckoCollector (15), RSSCollector (8)
- **Symbol format**: `BTCUSDT` → stripped to `BTC` by collector
- **Event assets**: `Asset(symbol="BTC", asset_class=AssetClass.CRYPTO, ...)`

### Scoring
- **ScoreEngine**: Base relevance = 70 (highest tier). Always passes `min_score=40`.
- **Result**: Passes to agent swarm.

### Agent Analysis
- **MarketAgent**: `_fetch_ohlcv("BTC")` → Binance API returns OHLCV data. Full technical analysis.
- **RiskAgent**: `_fetch_ohlcv("BTC")` → Binance API returns OHLCV data. Volatility, ATR, VaR computed.
- **Other agents**: NewsAgent processes crypto events, MacroAgent evaluates, TrendAgent evaluates.

### Council
- **AgentCouncil v2**: Collects all agent opinions, produces `CouncilDecision`.
- **MetaCouncil**: If disagreement, escalates (rare for crypto with clear signals).

### Execution
- **PaperTradingEngine.process_decision()**:
  - Extracts `symbol` and `price` from opinion metadata
  - Validates symbol against `current_prices` dict
  - Creates `TradeSignal` with stop-loss, take-profit
  - Engine.update_market_data("BTC", price) → updates GapRisk, CrashDetector
  - CapitalGuard evaluates the trade
  - Trade is executed (paper)

### Blocking Points
- **None** — crypto is fully operational.

---

## FOREX — STOPS AT COUNCIL

### Data Collection
- **Sources**: YahooFinanceCollector (8 pairs), RSSCollector (3)
- **Symbol format**: `EURUSD=X` (Yahoo), `EURUSD` (RSS)
- **Event assets**: `Asset(symbol="EURUSD=X", asset_class=AssetClass.FOREX, ...)`

### Scoring
- **ScoreEngine**: Base relevance = 50 (reduced for non-crypto). May pass `min_score=40`.
- **Result**: Passes if no other score modifiers drag it below 40.

### Agent Analysis
- **MarketAgent**: `_fetch_ohlcv("EURUSD")` → Binance API fails → falls back to yfinance → returns EURUSD=X OHLCV. Analysis succeeds.
- **RiskAgent**: Same yfinance OHLCV fallback. Analysis succeeds.
- **Result**: AgentOpinions are created with FOREX metadata.

### Council
- **AgentCouncil v2**: Processes opinions, produces `CouncilDecision` with FOREX action.
- **Result**: Passes council.

### Execution — BLOCKED
- **PaperTradingEngine.process_decision()**:
  - Extracts `symbol = "EURUSD"` or `symbol = "EURUSD=X"` from metadata
  - `update_market_data("EURUSD", price)` is called
  - ⚠️ GapRisk, CrashDetector do NOT accept non-BTC symbols (hardcoded `symbol.upper() == "BTC"`)
  - Engine has no concept of forex session hours, swap rates, or leverage
  - Engine's `_calculate_position_size()` uses crypto-specific ATR thresholds
  - `symbol` is not a known crypto → engine has no execution confidence
  - **TradeSignal creation will fail** because the engine cannot determine valid stop/target levels for spot forex with crypto model

### Exact Blocking Point
```
core/execution/paper_trading.py:117 — symbol extraction from metadata succeeds
core/execution/paper_trading.py:167 — process_decision calls create_signal
core/execution/paper_trading.py:190 — create_signal uses crypto ATR logic → inappropriate for forex
Engine has no forex market profile → cannot validate forex trade parameters
```
**Forex trades are blocked by**: No forex market profile, no forex risk model, no forex-specific position sizing, missing low-level gap risk coverage.

---

## STOCKS — STOPS AT COUNCIL

### Data Collection
- **Sources**: YahooFinanceCollector (22 stocks), RSSCollector (10)
- **Symbol format**: `AAPL` (plain ticker)
- **Event assets**: `Asset(symbol="AAPL", asset_class=AssetClass.STOCK, ...)`

### Scoring
- **ScoreEngine**: Base relevance = 50. Passes for most stock events.

### Agent Analysis
- **MarketAgent**: `_fetch_ohlcv("AAPL")` → Binance fails → yfinance returns AAPL OHLCV. Analysis succeeds (trend, RSI, ATR all computed).
- **RiskAgent**: Same OHLCV path. Can compute volatility for stocks.
- **Result**: AgentOpinions created.

### Council
- Passes council with STOCK decisions.

### Execution — BLOCKED
- **PaperTradingEngine**: Same blocking pattern as FOREX:
  - `update_market_data("AAPL", price)` — GapRisk: only tracks BTC
  - Symbol unknown — no market profile to validate
  - No market hours awareness (would trade AAPL at 2 AM Saturday)
  - No earnings gap risk (would not widen stops before earnings)
  - No dividend adjustment
  - No short-sale restriction check

### Exact Blocking Point
```
core/execution/paper_trading.py:62 — update_market_data only handles BTC for GapRisk
core/execution/paper_trading.py:117 — symbol unknown to engine
No stock market profile → no session validation → no earnings gap awareness
```

---

## COMMODITIES — STOPS AT COUNCIL

### Data Collection
- **Sources**: YahooFinanceCollector (8 futures), RSSCollector (3)
- **Symbol format**: `GC=F` (Yahoo), `GOLD` (RSS)
- **Event assets**: `Asset(symbol="GC=F", asset_class=AssetClass.COMMODITY, ...)`

### Scoring
- **ScoreEngine**: Base relevance = 50. Passes.

### Agent Analysis
- **MarketAgent**: `_fetch_ohlcv("GC=F")` → Binance fails → yfinance returns GC=F OHLCV. Analysis succeeds.
- **RiskAgent**: Same. Can compute commodity volatility.
- **Result**: AgentOpinions created.

### Council
- Passes council with COMMODITY decisions.

### Execution — BLOCKED
- **PaperTradingEngine**: Same pattern + additional commodity-specific issues:
  - Futures rollover risk — GC=F price jumps on contract expiry
  - Engine has no concept of contango/backwardation
  - No expiry calendar
  - No storage cost awareness
  - Commodity-specific gap risk (inventory reports)

### Exact Blocking Point
```
core/execution/paper_trading.py:62 — GapRisk only tracks BTC
core/execution/paper_trading.py:117 — symbol unknown
No commodity market profile → no futures rollover → no expiry calendar
```
---

## BONDS — STOPS AT SCORE ENGINE

### Data Collection
- **Sources**: FREDCollector (4 rate series)
- **Symbol format**: `DGS10`, `DGS2`, `T10Y2Y`, `DFF`
- **Event assets**: `Asset(symbol="DGS10", asset_class=AssetClass.BOND, ...)`

### Scoring — BLOCKED
- **ScoreEngine**: Base relevance = 50 (BOND tier).
- **Problem**: Bond yields are macro indicators, not tradeable instruments.
- **At risk**: Relevance score may dip below `min_score=40` depending on context.

### Agent Analysis (if it passed)
- **MarketAgent**: `_fetch_ohlcv("DGS10")` → Binance fails → yfinance returns nothing useful → **no OHLCV available**. Agent returns `None`.
- **RiskAgent**: Same — no OHLCV means no risk calculation.

### Council
- Would not produce a tradeable decision even if reached — agents cannot analyze without price data.

### Execution
- Not reachable.
- Would be blocked by: no tradeable instrument (bonds are yield series), no OHLCV provider, no position sizing model for fixed income.

### Exact Blocking Point
```
core/engines/score_opportunity.py:# — ScoreEngine._calculate_asset_relevance returns 50
May not reach min_score threshold of 40
Even if it passed: agents have no OHLCV data source for bond symbols
```

---

## INDICES — STOPS AT SCORE ENGINE

### Data Collection
- **Sources**: YahooFinanceCollector (8 indices), FREDCollector (9 economic), PolymarketCollector (dynamic)
- **Symbol format**: `^GSPC` (Yahoo), `CPIAUCSL` (FRED)
- **Event assets**: `Asset(symbol="^GSPC", asset_class=AssetClass.INDEX, ...)`

### Scoring — BLOCKED
- **ScoreEngine**: Base relevance = 50 (INDEX tier). Same BOND risk.

### Agent Analysis (if it passed)
- **MarketAgent**: `_fetch_ohlcv("^GSPC")` → Binance fails → yfinance returns SPX OHLCV. Analysis technically works, but trade on S&P 500 index cannot be executed directly — requires futures or ETF.
- **RiskAgent**: Same OHLCV path.
- **Result**: Agent opinions would recommend BUY/SELL on an index with no executable instrument.

### Execution
- Not reachable.
- Would be blocked by: index is not directly tradeable, requires futures/ETF mapping, no index futures rollover model.

### Exact Blocking Point
```
core/engines/score_opportunity.py — ScoreEngine._calculate_asset_relevance returns 50
Same score threshold risk as BONDS
Even if passed: indices like ^GSPC cannot be traded directly — would need SPX futures or SPY ETF
```

---

## Summary Blocking Matrix

| Asset Class | Collection | Scoring | Agents | Council | Execution | Primary Blocker |
|---|---|---|---|---|---|---|
| CRYPTO | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| FOREX | ✅ | ⚠️ | ⚠️ | ✅ | ❌ | No forex market profile in execution layer |
| STOCKS | ✅ | ⚠️ | ⚠️ | ✅ | ❌ | No stock market profile in execution layer |
| COMMODITIES | ✅ | ⚠️ | ⚠️ | ✅ | ❌ | No commodity profile + futures rollover |
| BONDS | ✅ | ❌ | ❌ | — | — | No OHLCV, no tradeable instrument |
| INDICES | ✅ | ❌ | ❌ | — | — | Cannot trade index directly |

Legend: ✅ = Works, ⚠️ = Works with limitations, ❌ = Blocked, — = Not reached
