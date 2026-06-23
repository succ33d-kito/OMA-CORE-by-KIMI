# OSIRIS / OMA-CORE Current Architecture Map

Generated: 2026-06-23

## Data Flow Diagram

```
WorldMonitorV2
  (CoinGecko, YahooFinance, Binance, FRED, RSS, Sentiment, Polymarket)
       │
       ▼
   EventBus
  (EVENTS_RAW → subscribed agents)
       │
       ├──────────────────────────────────────────────────┐
       ▼                                                  ▼
   NewsAgent    MacroAgent    MarketAgent    RiskAgent    TrendAgent
  (news/geo)    (macro/earn)  (RSI/SMA/ATR)  (vol/risk)   (EMA cross)
       │              │            │             │            │
       └──────────────┴────────────┴─────────────┴────────────┘
       │ Each produces AgentOpinion (opinion + confidence + conviction)
       ▼
   AgentCouncil v2
  (weighted voting, confidence × track record, min 2 opinions)
       │
       ▼
   MetaCouncil
  (3-profile cross-evaluation: Trader, Entrepreneur, Creator)
       │
       │ CouncilDecision → TradeSignal
       ▼
   PaperTradingEngine
  (process_decision → execute_signal → Trade)
       │
       ├── CapitalGuard (drawdown limits, kill switch → HALT)
       ├── CrashDetector v2 (6h/24h/72h multi-window → PANIC)
       ├── DirectionController (rolling WR → direction disable)
       ├── KnifeDetector (bounce quality → falling_knife)
       ├── GapRiskEngine (overnight gap → stop cushion)
       └── SlippageEngine (spread model → adjusted fills)
       │
       ▼
   PerformanceMemory
  (trade attribution, agent track records, accuracy calibration)
       │
       ▼
   Monitoring / Telemetry / Reports
  (HealthMonitor, TelemetryRecorder, GuardAuditRecorder,
   ExecutionAuditRecorder, FailureClassifier)
```

## Main Modules

| Module | Location | Role |
|--------|----------|------|
| `core/cli/main.py` | CLI entry point | Commands: collect, process, opportunities, events, status, watch, export, run, council |
| `core/config/config.py` | Configuration | Env-based settings via python-dotenv |
| `core/event_bus/bus.py` | EventBus | Pub/sub message bus, 12 topics, 1000 msg history |
| `core/schemas/event_schema.py` | Event model | Event, Asset, enums (EventType, AssetClass, Sentiment, Urgency) |
| `core/schemas/agent_schema.py` | Agent protocol | AgentOpinion, CouncilDecision, AgentRole, CouncilTier, Recommendation |
| `core/schemas/trade_schema.py` | Trade bridge | TradeSignal, Trade, TradeDirection, TradeStatus, ExitReason |
| `core/database/db.py` | OMACoreDatabase | SQLite3: events, opportunities, user_profiles |
| `core/collectors/world_monitor_v2.py` | Collector orchestrator | Runs 7 collectors, publishes to EventBus |
| `core/agents/news_agent.py` | NewsAgent | NEWS/GEOPOLITICAL/REGULATORY/HACK/SOCIAL sentiment analysis |
| `core/agents/macro_agent.py` | MacroAgent | MACRO/EARNINGS analysis, 30+ indicators |
| `core/agents/market_agent.py` | MarketAgent | Technical analysis (RSI, SMA, ATR, momentum, volume), candidate-based signal scoring |
| `core/agents/risk_agent.py` | RiskAgent | Volatility regime, drawdown risk, scenario risk, position sizing |
| `core/agents/trend_agent.py` | TrendAgent | EMA crossover (20/50/200), 6-point alignment count |
| `core/council/council.py` | AgentCouncil v2 | Weighted consensus, min 2 opinions, risk weighting |
| `core/council/meta_council.py` | MetaCouncil | Cross-profile conviction multipliers |
| `core/execution/paper_trading.py` | PaperTradingEngine | Simulated execution, SL/TP, trailing, max positions, guard integration |
| `core/execution/crash_detector.py` | CrashDetector v2 | Multi-window drawdown velocity, acceleration, ATR, volume |
| `core/execution/capital_guard.py` | CapitalGuard | Loss limits, drawdown thresholds, kill switch, guard modes |
| `core/execution/direction_controller.py` | DirectionController | Rolling WR tracking, direction disable <25% |
| `core/execution/gap_risk.py` | GapRiskEngine | Weekend gap modeling, stop cushion adjustment |
| `core/execution/slippage.py` | SlippageEngine | Spread model (per-asset bps) |
| `core/execution/knife_detector.py` | KnifeDetector | Bounce quality, volume profile, momentum, volatility contraction |
| `core/execution/performance_memory.py` | PerformanceMemory | Trade attribution, agent track records, confidence calibration |
| `core/memory/memory.py` | MemoryStore | ShortTermMemory (TTL), LongTermMemory (tagged) |
| `core/monitoring/telemetry.py` | Telemetry | TelemetryRecorder, GuardAuditRecorder, ExecutionAuditRecorder (JSONL append) |
| `core/monitoring/health.py` | HealthMonitor | 10 checks: equity, guard, crash, positions, price data, cycle diversity, skips |
| `core/monitoring/failure_classifier.py` | FailureClassifier | 9 categories, 4 severities, keyword-classification, JSONL recording |
| `core/engines/score_opportunity.py` | ScoreEngine v1 | Legacy: 6-weight scoring, opportunity engine, pipeline |

## Entry Points

| Name | Command | Description |
|------|---------|-------------|
| CLI | `python -m core.cli.main [command]` | Full pipeline control |
| Extended Demo | `python scripts/extended_demo_realtime.py --smoke` | 7-day smoke run harness |
| Extended Demo | `python scripts/extended_demo_realtime.py --run` | 30-day validation run |
| Report generator | `python scripts/extended_demo_report.py` | Report generation from JSONL |
| Dashboard | `python dashboard/app.py` | Flask web UI (port 5000) |
| Cron | `bash run_oma_cron.sh` | Scheduled runs |

## Output Files

| File | Format | Content |
|------|--------|---------|
| `oma_core.db` | SQLite3 | events, opportunities, user_profiles |
| `_extended_demo/telemetry_*.jsonl` | JSONL | Per-cycle pipeline telemetry |
| `_extended_demo/guard_audit_*.jsonl` | JSONL | Guard intervention records |
| `_extended_demo/execution_audit_*.jsonl` | JSONL | Execution block records |
| `_extended_demo/failures_*.jsonl` | JSONL | Classified failure records |
| `_extended_demo/run_state.json` | JSON | Persistent cycle counters |
| `logs/oma-core.log` | Text | INFO+ structured logs |
| `logs/oma-core-errors.log` | Text | ERROR+ logs |
| `logs/oma-core-debug.log` | Text | DEBUG+ logs |
| `docs/data.json` | JSON | GitHub Pages data export |

## Runtime State Files

| File | Content |
|------|---------|
| `_extended_demo/run_state.json` | cycle_id, cumulative counters (events, signals, trades, errors, blocks, guards) |
| `.env` | API keys (FRED, Telegram) |

## Telemetry Data Lineage

```
DemoHarness (each cycle)
  → TelemetryRecorder.record()     → telemetry_*.jsonl
  → GuardAuditRecorder.record()    → guard_audit_*.jsonl
  → ExecutionAuditRecorder.record()→ execution_audit_*.jsonl
  → FailureClassifier.record()     → failures_*.jsonl
  → run_state.json (state persistence)

HealthMonitor.run_all()
  → prints health status to console
  → overall_status() → HEALTHY/DEGRADED/CRITICAL
```

## Test Organization

22 test files, 281 tests total:
- Agent/council tests: 18 (agent_council + agent_schema + council_v2)
- Backtest: 7
- Crash detection: 21
- Crypto regression: 42
- Execution/guards: 35 (kill_switch + knife_detector + survival_replay)
- Market agent signal integrity: 13
- Monitoring: 81 (health_monitor + telemetry + failure_classifier)
- Paper trading: 18 (paper_trading + performance_memory)
- Other: 46 (event_bus, integration, memory, profiles, risk_agent, trade_schema, market_agent)
