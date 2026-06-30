# Performance Audit

## Static hotspot scan

| Pattern | Hits | Examples |
|---|---|---|
| sleep_loop | 5 | setup.py:859 time.sleep(args.interval)<br>scripts/extended_demo_realtime.py:630 time.sleep(self.interval)<br>backups/v2.0/setup.py:859 time.sleep(args.interval)<br>tests/test_memory.py:17 time.sleep(1.5)<br>core/cli/main.py:210 time.sleep(args.interval) |
| while_true | 3 | setup.py:845 while True:<br>backups/v2.0/setup.py:845 while True:<br>core/cli/main.py:196 while True: |
| file_write | 93 | export_for_github.py:66 with open(json_path, 'w', encoding='utf-8') as f:<br>export_for_github.py:67 json.dump(data, f, ensure_ascii=False, indent=2)<br>setup.py:868 with open(filename, "w", encoding="utf-8") as f:<br>setup.py:869 json.dump(opps, f, indent=2, default=str)<br>setup.py:876 with open(filename, "w", newline="", encoding="utf-8") as f:<br>setup.py:963 with open(full, 'w', encoding='utf-8') as f:<br>scripts/audit_priority_consistency.py:330 with open(path, "w", encoding="utf-8") as f:<br>scripts/asset_coverage_audit.py:397 with open(output, "w") as f:<br>scripts/asset_coverage_audit.py:398 json.dump(report, f, indent=2, default=str)<br>scripts/historical_learning_replay.py:129 path.write_text("\n".join(lines), encoding="utf-8") |
| requests | 16 | setup.py:331 self.session = requests.Session()<br>scripts/audit_score_saturation.py:336 "on all FRED requests. This reduces diversity of macro events."<br>backups/v2.0/setup.py:331 self.session = requests.Session()<br>tests/test_telegram_notifier.py:387 with patch("core.engines.telegram_notifier.requests.post") as mock_post:<br>tests/test_telegram_notifier.py:397 with patch("core.engines.telegram_notifier.requests.post") as mock_post:<br>tests/test_telegram_notifier.py:432 with patch("core.engines.telegram_notifier.requests.get") as mock_get:<br>core/agents/market_agent.py:271 resp = requests.get(url, params=params, timeout=10)<br>core/agents/risk_agent.py:202 resp = requests.get(url, params={"symbol": pair, "interval": "1h", "limit": 100}, timeout=10)<br>core/collectors/world_monitor.py:22 self.session = requests.Session()<br>core/collectors/base_collector.py:12 self.session = requests.Session() |
| sqlite | 94 | export_for_github.py:7 import sqlite3<br>export_for_github.py:15 conn = sqlite3.connect(db_path)<br>export_for_github.py:16 conn.row_factory = sqlite3.Row<br>migrate_to_postgres.py:3 import sqlite3<br>migrate_to_postgres.py:87 sqlite_conn = sqlite3.connect("oma_core.db")<br>migrate_to_postgres.py:88 sqlite_conn.row_factory = sqlite3.Row<br>setup.py:176 import sqlite3, json, uuid<br>setup.py:190 conn = sqlite3.connect(self.db_path)<br>setup.py:191 conn.row_factory = sqlite3.Row<br>scripts/audit_priority_consistency.py:14 import sqlite3 |
| pandas_iterrows | 5 | scripts/research_sprint.py:108 for idx, r in hist.iterrows()<br>scripts/slippage_test.py:44 for idx, r in hist.iterrows()]<br>core/agents/market_agent.py:298 for idx, row in hist.iterrows()<br>core/agents/risk_agent.py:210 return [{"close": float(r["Close"]), "high": float(r["High"]), "low": float(r["Low"]), "volume": float(r["Volume"])} for _, r in hist.iterrows()]<br>core/execution/backtest_engine_v2.py:92 for idx, r in hist.iterrows() |
| network_clients | 184 | render_app.py:5 import psycopg2<br>render_app.py:14 return psycopg2.connect(DATABASE_URL, sslmode='require')<br>migrate_to_postgres.py:4 import psycopg2<br>migrate_to_postgres.py:89 pg_conn = psycopg2.connect(database_url, sslmode='require')<br>setup.py:323 import requests, feedparser, json, uuid<br>setup.py:331 self.session = requests.Session()<br>scripts/asset_coverage_audit.py:24 # BinanceCollector<br>scripts/asset_coverage_audit.py:25 binance_symbols = [<br>scripts/asset_coverage_audit.py:30 collectors["binance"] = {<br>scripts/asset_coverage_audit.py:32 "symbols": [s.replace("USDT", "") for s in binance_symbols], |


## CPU hotspots

- Scoring, backtesting, scientific evaluation, and data-frame operations are likely CPU hotspots.
- `iterrows` usage exists in scripts, which is inefficient for large data.

## Memory hotspots

- Collectors and CLI process batches in memory.
- Long-running watch mode may accumulate state indirectly through DB/files/logs.

## IO hotspots

- SQLite operations, report generation, JSON/CSV exports, and repeated source fetches are primary IO surfaces.
- No global caching layer or request de-duplication guarantee is evident.

## Blocking operations

- CLI watch mode is blocking and sleep-loop based.
- External network calls appear synchronous.

## Verdict

Performance is sufficient for local/small-scale research, not certified for production scale, multi-market throughput, or long-running autonomous operation.
