# BTCUSDT USDⓈ-M Futures: frozen 2024→2025 gate

## Provenance and preflight

The attached `BTCUSDT_1h_Cleaned.csv` has SHA-256 `201a3b15d50a791cb5be2b755107c8303906c8fc3ca6b64e8377c9fc73ba016b` and Git blob SHA-1 `629859ca96ea5e13816c10ce74bdd48e01ba93dd`, matching the specified repository blob. The 2024 extraction contains exactly 8,784 consecutive UTC hourly opens from 2024-01-01 00:00 through 2024-12-31 23:00, zero duplicate or missing hours, finite positive OHLC, coherent high/low bounds, finite nonnegative volume, and no imputation. See the normalized CSV and its SHA-256 manifest.

All twelve official Binance Vision USDⓈ-M Futures BTCUSDT 1h monthly ZIPs passed their corresponding official SHA-256 CHECKSUM files. All 8,784 timestamps and all five OHLCV numeric fields agree **exactly** with the supplied CSV (zero mismatches). The archives, CHECKSUMs and audit are bundled under `official_2024/`.

**Important correction to the earlier snapshot:** its 2025 `research/data/BTCUSDT_1h_2025.json` does not equal the supplied USDⓈ-M Futures series; the first 2025 bar already differs. It is excluded from this longitudinal comparison. The same frozen algorithm was rerun on the 8,760 hours of 2025 from the attached futures CSV. The original exploratory 2025 files remain intact for audit. Neither feature thresholds nor bins, horizons, n≥50, 24-observation bootstrap, 1,000 resamples or seed 1729 were adjusted.

## Results

| Frozen ablation | Paired cells × horizons (n≥50 each year) | Sign persistence | Median effect magnitude ratio | Median cell coverage 2024 / 2025 | Same-sign intervals excluding zero in both years |
|---|---:|---:|---:|---:|---:|
| Regime | 65 | 33/65 = 50.8% | 0.316 | 4.46% / 5.52% | 0 |
| Regime + OI | 120 | 48/120 = 40.0% | 0.374 | 3.44% / 3.38% | 0 |
| Regime + Positioning | 105 | 52/105 = 49.5% | 0.395 | 3.39% / 3.76% | 2 |
| Regime + Taker Flow | 120 | 51/120 = 42.5% | 0.397 | 3.31% / 3.45% | 1 |
| Regime + OI + Positioning | 185 | 90/185 = 48.6% | 0.377 | 1.89% / 2.12% | 2 |
| Regime + OI + Positioning + Taker Flow | 270 | 138/270 = 51.1% | 0.377 | 1.37% / 1.41% | 7 |

`effect magnitude ratio` is min(|2024 mean|, |2025 mean|)/max(|2024 mean|, |2025 mean|) on n≥50 paired cells. It is descriptive: a more fragmented variant changes the population of eligible cells. Coverage is per cell, not total panel coverage. The panels contain 2024 and 2025 decisions with metrics available at the hour boundary, after an 80-bar OHLCV warmup. Full per-cell sample sizes, coverage, means, positive-return fractions and moving-block confidence intervals at 1/4/12/24/48 hours are in the two ablation tables and paired table.

The baseline flips in 32/65 eligible cells × horizons. New partitions do not consistently eliminate flips; their comparable subcells both resolve and introduce flips (`FLIP_ATTRIBUTION_DESCRIPTIVE.csv`). This is descriptive, since each parent is counted multiple times among children. It does not prove the new variables explain the earlier 2025→2026 flips, which are a separate period/venue analysis.

## Fragmentation, multiplicity and decision

The number of cells rises from 18–19 in Regime to 147/140 (2024/2025) with all variables, while median 2025 cell coverage falls from 5.52% to 1.41%. The 95% intervals are **unadjusted** across hundreds of overlapping cell/horizon comparisons, and the inherited per-cell moving block resamples selected observations rather than uninterrupted calendar blocks. The 7 apparent same-sign interval pairs in the largest variant are not familywise evidence. We apply a conservative multiplicity gate: no individual or aggregate positive discovery is accepted from these unadjusted comparisons. No threshold was tuned after seeing 2024.

**Gate decision: FAIL; no Knowledge, Criterion or trading promotion.** OI and Taker Flow worsen sign persistence against Regime. Positioning also falls slightly short. The full combination improves the descriptive percentage by only 0.3 percentage points while fragmenting coverage roughly fourfold; this does not establish stable incremental Edge. Positive findings are source authenticity, clean continuous OHLCV, exact official match and reproducible causal evaluation. Negative findings are unstable signs, weak magnitude transport and multiplicity/fragmentation.

Further Criterion candidacy would require a predeclared, low-dimensional hypothesis; simultaneous or familywise inference on calendar-resampled dependent returns; untouched prospective data; independent venue/instrument evidence; next-open execution with costs and risk controls; and the remaining ADR-OMA-V2-005 gates. These analyses must be designed before viewing the future holdout.
