# BTCUSDT public metrics: causal research audit (29 September 2026)

## Integrity and availability

The Parquet SHA-256 equals `db5959a0e38d8155ee5931a5a22fb04b6ed3af853faba01fe498f65d17ea37ce`. It contains 592,934 rows, seven fields, and observations from 2020-09-01 00:00 UTC through 2026-04-24 00:00 UTC. There are no duplicate timestamps or reversed rows. The audit records 2,989 intervals longer than five minutes, representing 641 full missing five-minute slots under the documented floor rule; 3,056 timestamps are off the exact five-minute grid. Null counts are 92,226 top-account, 92,192 top-position, 5,797 global and 37,271 taker ratios. OI has 502 nonpositive values; OI value has 514. Taker ratio has one additional nonpositive value beyond its nulls. No value was imputed.

The original observations are preserved in `BTCUSDT_metrics_5m.csv.gz`. The valid complete-case hourly metrics panel excludes 412 invalid rows during 2024–2025, leaving 8,773 decisions in 2024 and 8,757 in 2025 out of 8,784 and 8,760 expected hours. Each hourly decision uses the last actual metric observation in the preceding completed hour. The metric timestamp and its age remain in the output.

## Frozen evaluation and findings

The repository includes 8,760 2025 OHLCV bars, but **no raw 2024 OHLCV**. This blocks 2024 forward returns and a genuine 2024→2025 transfer test. It also blocks a defensible claim that the new variables explain the previously reported seven sign flips between 2025 and 2026. Those flips are a distinct earlier comparison and cannot be reclassified using 2024–2025 metrics alone.

The exploratory 2025 joined panel has 8,676 complete causal decisions. All six prescribed ablations were run at 1, 4, 12, 24 and 48 hours. Of 1,690 cell/horizon rows, 925 meet n≥50. The detailed `ABLATION_2025_EXPLORATORY.csv` reports sample size, coverage, mean conditional next-open-to-future-close return, positive-return fraction, and 95% moving-block intervals (24 observations; 1,000 resamples). Qualified cells whose unadjusted interval excludes zero: Regime 2/70; +OI 8/120; +Positioning 10/120; +Taker 11/120; +OI+Positioning 30/215; all variables 45/280. More partitions create more apparent discoveries. These are overlapping horizons, multiple uncorrected comparisons, and selected-cell blocks do not represent uninterrupted calendar time. They are **not evidence of improvement**, and cannot establish sign persistence, effect-size stability or predictive trading performance. No retrospective threshold changes were made.

## Positive and negative results

- Positive: source integrity verified; normalized historical metrics and a causal 2024–2025 hourly feature panel are reproducible; 2025 exploratory partitions and confidence intervals are available for audit.
- Negative: the Parquet contains substantial nulls, invalid zeros, displaced timestamps and gaps; trade-count Participation cannot be computed from the available six-column OHLCV feed, so only the existing volume-based Market Context participation descriptor is present; the confirmatory comparison and flip explanation remain unidentifiable.

## Decision

**No promotion** to Knowledge, Criterion or trading execution. Regime, MarketState and Market Context use the repository's existing implementations; the provider adapter carries Binance-specific field names. Longitudinal Stability remains a gate rather than a fabricated 2024 score. The next scientifically valid input is source-verified BTCUSDT 2024 H1 OHLCV with a SHA-256 manifest; rerun the same frozen code and compare independent periods before prospective and execution gates.
