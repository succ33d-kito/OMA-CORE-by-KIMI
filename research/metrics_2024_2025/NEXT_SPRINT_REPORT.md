# Statistical repair and prospective protocol

The 2024→2025 result remains a failed historical gate. No new historical return analysis was used to select a threshold or feature combination in this sprint.

`core/scientific/calendar_block_inference.py` implements joint calendar-time moving-block bootstrap across the five horizons, with a max-standardized-deviation simultaneous confidence family. The whole hourly timeline is sampled; absent hours stay absent. Tests exercise reproducibility, missing hours, overlap rejection, insufficient sample and duplicate time rejection. The older per-cell intervals remain in their original tables and are not relabeled as corrected.

A first trend-up proposal was rejected on exposure counts alone: only 37 and 31 target hours in 2024 and 2025. The frozen forward hypothesis uses Regime `range`, rising OI and taker ratio above 1 versus other valid range observations. Historical exposure counts are 1,318/1,153 target hours and 3,954/4,110 comparator hours (2024/2025). Those counts establish feasibility only, not predictive value. No retrospective conditional returns for this new comparison were inspected. The registered five-horizon inference uses 168-hour blocks, 2,000 replicates, n≥200 per arm, and 4h as the primary horizon, with a 10-basis-point research cost hurdle.

The forward evaluator requires actual `available_at` timestamps for each H1 bar and metric. It decides five minutes after a completed bar, uses only data received by then, and measures an entry at the next full hour's open. It rejects historical decisions, incomplete bars, late inputs, changed protocol bytes, insufficient duration or N. The previous Binance Vision archive does not include independently logged receipt times and is ineligible for this prospective gate.

An end-to-end synthetic 3,500-hour feed exercised the pipeline: 3,371 eligible decisions, 1,263 target, 2,104 comparator, no missing calendar hours, and no research pass. Synthetic data is a functional check and provides no market evidence. Criterion and trading remain blocked pending real prospective collection, source verification, independent replication and measured execution costs.
