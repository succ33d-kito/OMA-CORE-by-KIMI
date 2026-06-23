# OSIRIS Multi-Market Asset Coverage Report

> Generated: 2026-06-23  
> Source: `scripts/asset_coverage_audit.py` static code analysis

---

## Executive Summary

| Metric | Value |
|---|---|
| Total collectors | 7 |
| Asset classes collected | 6 (crypto, forex, stock, commodity, index, bond) |
| Total observed symbols | 115 |
| Assets tradeable | 15 crypto (spot only) |
| Assets observed but not tradeable | 100 |

---

## Symbols by Asset Class

| Asset Class | Symbols | Sources |
|---|---|---|
| **Crypto** | 39 | Binance (15), CoinGecko (15), RSS (8), Sentiment (1) |
| **Stock** | 32 | Yahoo Finance (22), RSS (10) |
| **Forex** | 11 | Yahoo Finance (8), RSS (3) |
| **Commodity** | 11 | Yahoo Finance (8), RSS (3) |
| **Index** | 18 | Yahoo Finance (8), FRED (9), Polymarket (1) |
| **Bond** | 4 | FRED (4) |

---

## Collector Coverage

### BinanceCollector (CRYPTO)
- **Symbols**: BTC, ETH, SOL, XRP, BNB, ADA, DOGE, AVAX, LINK, MATIC, DOT, UNI, LTC, BCH, ATOM
- **Format**: TICKERUSDT (e.g., BTCUSDT)
- **OHLCV**: Native — primary data source for MarketAgent/RiskAgent

### CoinGeckoCollector (CRYPTO)
- **Symbols**: Top 50 by market cap (same 15 core symbols as Binance)
- **Use**: Price data, metadata enrichment

### YahooFinanceCollector (MULTI)
- **Stocks** (22): AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, AMD, INTC, CRM, ADBE, PYPL, UBER, COIN, PLTR, SPY, QQQ, IWM, DIA, VTI, VOO
- **Forex** (8): EURUSD=X, GBPUSD=X, USDJPY=X, USDCHF=X, AUDUSD=X, USDCAD=X, NZDUSD=X, EURGBP=X
- **Commodities** (8): GC=F, SI=F, CL=F, NG=F, HG=F, ZW=F, ZC=F, ZS=F
- **Indices** (8): ^GSPC, ^IXIC, ^DJI, ^RUT, ^VIX, ^FTSE, ^N225, ^HSI

### FREDCollector (BOND + INDEX)
- **Bonds** (4): DFF, DGS10, DGS2, T10Y2Y
- **Indices** (9): CPIAUCSL, CPILFESL, PCEPI, PAYEMS, UNRATE, ICSA, GDP, GDPC1, INDPRO, UMCSENT

### RSSCollector (MULTI)
- **Sources**: Reuters, Bloomberg, CoinDesk, CoinTelegraph, ForexLive, CNBC, MarketWatch
- **Symbol map**: 8 crypto, 10 stocks, 3 forex, 3 commodities
- **Key**: Text-based asset extraction — quality depends on news content

### SentimentCollector (INDEX)
- **Symbol**: FNG-CRYPTO (Crypto Fear & Greed Index)
- **Not tradeable** — informational only

### PolymarketCollector (INDEX)
- **Symbols**: Dynamic prediction market events
- **Not tradeable** — informational only

---

## Duplicate Symbol Table

Symbols that appear from multiple sources (potential for double-counting):

| Symbol | Counted As | Sources |
|---|---|---|
| BTC | crypto | Binance, CoinGecko, RSS |
| ETH | crypto | Binance, CoinGecko, RSS |
| SOL | crypto | Binance, CoinGecko, RSS |
| XRP | crypto | Binance, CoinGecko, RSS |
| AAPL | stock | Yahoo Finance, RSS |
| MSFT | stock | Yahoo Finance, RSS |
| EURUSD | forex | Yahoo Finance (EURUSD=X), RSS (EURUSD) |
| GOLD | commodity | RSS (GOLD) = Yahoo (GC=F) — NORMALIZATION GAP |

---

## Normalization Gaps Identified

1. **Forex symbol mismatch**: Yahoo `EURUSD=X` vs RSS `EURUSD` — same instrument, different IDs
2. **Commodity symbol mismatch**: Yahoo `GC=F` (Gold futures) vs RSS `GOLD` — same instrument
3. **No exchange prefix**: Stock symbols lack exchange context (e.g., `AAPL` on NASDAQ vs other venues)
4. **No ISIN/CUSIP mapping**: No universal identifier to resolve cross-market conflicts
5. **Crypto-stock symbol collision risk**: A token like `XRP` could theoretically match a stock ticker

---

## Pipeline Stop Points

| Asset Class | Pipeline Status | Blocking Layer |
|---|---|---|
| CRYPTO | FULL FLOW | — |
| FOREX | STOPS AT COUNCIL | PaperTradingEngine rejects non-crypto symbols |
| STOCKS | STOPS AT COUNCIL | PaperTradingEngine rejects non-crypto symbols |
| COMMODITIES | STOPS AT COUNCIL | PaperTradingEngine rejects non-crypto symbols |
| BONDS | STOPS AT SCOREENGINE | Relevance score too low for execution path |
| INDICES | STOPS AT SCOREENGINE | Relevance score too low for execution path |

---

## Agent OHLCV Support

| Asset Class | Provider | Status | Limitations |
|---|---|---|---|
| CRYPTO | Binance API | Native | Always available for 15 pairs |
| STOCK | yfinance | Fallback | Rate-limited, no caching |
| FOREX | yfinance | Fallback | Yahoo notation (EURUSD=X) |
| COMMODITY | yfinance | Fallback | Yahoo notation (GC=F) |
| BOND | FRED | None | No OHLCV — only yield series |
| INDEX | yfinance | Fallback | Yahoo notation (^GSPC) |
