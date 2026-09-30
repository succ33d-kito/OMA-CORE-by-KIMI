# Reproducing the frozen 2024→2025 gate

From the repository root, install `requirements.txt`, `pyarrow` (for the older Parquet audit), and `pytest`. Then run:

```bash
python scripts/confirm_2024_metrics.py research/metrics_2024_2025/BTCUSDT_1h_Cleaned_source.csv --repo . --official research/metrics_2024_2025/official_2024
python -m pytest -q
```

The command first validates the supplied Git blob and all 8,784 2024 hours, verifies the twelve official ZIP CHECKSUMs and compares their OHLCV exactly, then computes the 2024 and same-venue 2025 panels using the frozen 2025 protocol. The source Parquet and older outputs remain bundled for independent replay. All input and principal output SHA-256 hashes appear in `confirmatory_manifest.json`. The earlier 2025 research price JSON is a different market series and must not enter this comparison.
