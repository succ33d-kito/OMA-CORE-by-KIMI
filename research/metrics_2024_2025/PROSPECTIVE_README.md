# Prospective research gate

The registered design is `PROSPECTIVE_H1_PREREGISTRATION.json`, protected by the SHA-256 in `PROSPECTIVE_PROTOCOL_SHA256.txt` and the evaluator. The rejected trend-up design is preserved separately because its exposure count was too small. Neither design was selected using new conditional-return results.

A future collector must record **actual receipt times** in UTC. Price CSV columns: `time,available_at,open,high,low,close,volume`, where `time` is the H1 bar opening time and `available_at` is when its completed bar reached the system. Metric CSV columns: `timestamp,available_at,sum_open_interest,sum_open_interest_value,count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,count_long_short_ratio,sum_taker_long_short_vol_ratio`. `available_at` is the observed receipt time, not a reconstructed timestamp. Retain raw collection logs and input SHA-256. The bar feed needs at least 80 hours of warmup before 2026-10-01, and at least 49 subsequent bars to mature the last 48h outcome.

After a minimum of 90 calendar days of genuinely prospective observations:

```bash
python scripts/prospective_oi_taker_gate.py FUTURE_H1_BARS.csv FUTURE_METRICS.csv --out research/prospective_run
```

The script fails closed for gaps, stale or late data, insufficient exposure N, or changed protocol. A passing research result remains separate from trading authorization. The prior historical datasets do not contain verified receipt timestamps and cannot be submitted as prospective data.

## Recording real receipts

From 2026-10-01 UTC onward, a collector can submit one JSON observation through `scripts/prospective_receipts.py record LEDGER.db bar|metric --source VERIFIED_PROVIDER` on standard input. The writer assigns `available_at`; input must not include it. Export and verify with `python scripts/prospective_receipts.py export LEDGER.db --out RECEIPT_CSV_DIR`, then use those CSVs with the frozen gate script. Run a separate source verification before treating a third-party feed as BTCUSDT USDⓈ-M Futures.

The optional `python scripts/binance_research_collect.py LEDGER.db --raw-dir RAW_RESPONSES` makes one poll, records a closed H1 bar and a complete aligned 5m metric bundle, and keeps the raw metrics responses. It has no order endpoints. In an eligible environment, a required market-data API key may be read from `BINANCE_API_KEY` without storing it in the ledger. Schedule single polls locally only after verifying local availability, endpoint permissions and rate limits. This Work environment returned HTTP 451; no scheduled collector or prospective data was created here. A Binance Vision archive downloaded later does not supply an earlier `available_at` and cannot replace missed polls.
