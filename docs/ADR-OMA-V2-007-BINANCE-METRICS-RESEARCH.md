# ADR-OMA-V2-007 — Public metrics research adapter

Status: accepted for research, no Knowledge/Criterion promotion.

The six Binance USD-M BTCUSDT metrics enter as timestamped observations through `core.market_mechanics.binance_public_metrics`. The raw Parquet is pinned by SHA-256. The normalized CSV preserves all original nulls and invalid values. The hourly research panel retains the last *valid, actually observed* record from a completed UTC hour, and exposes it only at the following hour boundary. Missing observations are not filled. The metric source is distinct from OHLCV provenance; provider-specific parsing stays in the adapter.

The 2024 OHLCV source is absent. Consequently, a 2024→2025 forward-return comparison and an explanation of previously reported sign flips cannot be inferred. The 2025 ablation is exploratory and selection contaminated. Frozen grouping definitions: Regime v1; OI rising/falling versus the previous *observed consecutive* hourly metric; positioning long if all three ratios exceed 1, short if all are below 1, otherwise mixed; taker buy/sell relative to 1. These are descriptive partitions, not trading rules. Forward returns use next bar open as entry and a future close, without execution costs; they are not PnL. Minimum cell size 50, moving blocks 24 consecutive observations, 1000 resamples, fixed seed 1729. No threshold search or promotion is permitted.

The full gate still requires source-verified 2024 hourly OHLCV, independent temporal comparison, prospective evidence, execution and cost testing, and the other gates in ADR-OMA-V2-005.

## 2024 confirmation outcome (2026-09-29)

The supplied Git blob was checked and the 2024 OHLCV matches all twelve official Binance Vision USDⓈ-M monthly archives after checksum verification. The original 2025 research OHLCV differs from the futures feed; the comparison was recomputed on 2025 futures from the same supplied blob with the frozen protocol. The longitudinal gate failed. Details, including negative results and fragmentation, are in `research/metrics_2024_2025/CONFIRMATORY_2024_2025_REPORT.md`.
