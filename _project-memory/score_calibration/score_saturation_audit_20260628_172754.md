# Score Saturation Audit Report

**Timestamp**: 2026-06-28T17:27:54.898006+00:00
**Database**: oma_core.db
**Opportunities**: 146
**Events**: 507

## Priority Distribution

- **CRITICAL**: 60
- **HIGH**: 55
- **LOW**: 4
- **MEDIUM**: 27
- **Critical %**: 41.1%
- **Saturated**: False

## Score Distribution

| Metric | Value |
|---|---|
| Count | 146 |
| Min | 40.6 |
| Max | 100.0 |
| Mean | 85.14 |
| Median | 87.75 |
| At 100 | 63 (43.2%) |
| Repeated score sets | 14 |

## Asset Anomalies

- **price_zero**: 58
- **pct_negative_100**: 58
- **missing_price**: 4
- **missing_return**: 12
- **malformed_assets**: 0

## Data Quality

- **data_quality_issues**: 0
- **data_quality_capped**: 0
- **yahoo_price_zero**: 0
- **yahoo_pct_negative_100**: 0
- **yahoo_malformed**: 0

## Source Breakdown

- **yahoo_finance**: 86
- **polymarket**: 80
- **rss_bloomberg**: 71
- **coingecko**: 67
- **rss_cnbc**: 58
- **rss_marketwatch**: 40
- **rss_cointelegraph**: 39
- **rss_coindesk**: 31
- **fred**: 18
- **binance**: 9
- **sentiment_fng_crypto**: 4
- **rss_forexlive**: 4

## Type Breakdown

- **SHORT_SETUP**: 52
- **WATCHLIST_ADD**: 42
- **MONITOR_MACRO**: 14
- **MACRO_HEADWIND**: 9
- **NEWS_DRIVEN**: 8
- **REGULATORY_TAILWIND**: 6
- **REGULATORY_HEADWIND**: 4
- **SENTIMENT_TURN_BEAR**: 4
- **MACRO_TAILWIND**: 3
- **AVOID_OR_SHORT**: 2
- **SAFE_HAVEN_FLOW**: 2

## Suspicious Patterns

- **score_100_plus_price_zero**: [SHORT_SETUP] AAPL -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] AAPL -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] MSFT -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] MSFT -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] GOOGL -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] GOOGL -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] AMZN -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] AMZN -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] TSLA -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] TSLA -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] NVDA -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] NVDA -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] META -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] META -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] NFLX -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] NFLX -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] AMD -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] AMD -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] INTC -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] INTC -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] CRM -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] CRM -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] ADBE -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] ADBE -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] PYPL -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] PYPL -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] UBER -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] UBER -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] COIN -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] COIN -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] PLTR -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] PLTR -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] SPY -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] SPY -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] QQQ -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] QQQ -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] IWM -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] IWM -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] DIA -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] DIA -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] VTI -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] VTI -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] VOO -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] VOO -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] EURUSD=X -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] EURUSD=X -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] GBPUSD=X -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] GBPUSD=X -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] USDCHF=X -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] USDCHF=X -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] EURGBP=X -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] EURGBP=X -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [MACRO_HEADWIND] S&P 500 -100.00% (count=1)
- **negative_100_percent**: [MACRO_HEADWIND] NASDAQ Composite -100.00% (count=1)
- **negative_100_percent**: [MACRO_HEADWIND] Dow Jones -100.00% (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] AAPL -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] AAPL -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] MSFT -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] MSFT -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] GOOGL -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] GOOGL -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] AMZN -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] AMZN -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] TSLA -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] TSLA -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] NVDA -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] NVDA -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] META -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] META -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] NFLX -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] NFLX -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] AMD -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] AMD -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] INTC -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] INTC -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] CRM -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] CRM -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] ADBE -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] ADBE -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] PYPL -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] PYPL -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] UBER -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] UBER -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] COIN -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] COIN -100.00% -- $0.00 (count=1)
- **score_100_plus_price_zero**: [SHORT_SETUP] PLTR -100.00% -- $0.00 (count=1)
- **negative_100_percent**: [SHORT_SETUP] PLTR -100.00% -- $0.00 (count=1)
- **repeated_conviction**: 84.0 (count=58)
- **repeated_conviction**: 88.75 (count=13)
- **repeated_conviction**: 67.5 (count=7)

## Root-Cause Hypotheses

1. Missing price data: Yahoo Finance or other price feeds returning $0.00. This inflates urgency/sentiment for price-movement events while the underlying data is invalid. Root cause: data source normalization bug or API rate limiting.
2. Failed data downloads treated as -100% returns: When Yahoo Finance fails to fetch price data, percent_change may be interpreted as -100%. This creates extreme bearish events that score highly.
3. Score clipping: 43.2% of scores are 100. The min(raw_score * multiplier, 100) cap in ScoreEngine is hit too frequently. Events with CRITICAL urgency (100) + strong sentiment + 1.3× macro multiplier exceed 100 before clipping.
