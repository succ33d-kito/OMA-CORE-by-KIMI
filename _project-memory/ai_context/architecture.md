# OSIRIS / O.M.A.-C.O.R.E. — Architecture

## Pipeline

```
WorldMonitorV2
  (7 collectors: CoinGecko, YahooFinance, Binance, FRED, RSS, Sentiment, Polymarket)
       │
       ▼
   EventBus
  (12 topics: EVENTS_RAW, EVENTS_PROCESSED, OPINIONS_AGENT, DECISIONS_COUNCIL, ...)
       │
       ▼
   Agent Swarm
  (NewsAgent, MacroAgent, MarketAgent, RiskAgent, TrendAgent)
  (Each produces AgentOpinion with confidence, conviction, evidence)
       │
       ▼
   AgentCouncil v2
  (Weighted voting: confidence × track record, min 2 opinions, risk weighting)
       │
       ▼
   MetaCouncil
  (3-profile evaluation: Trader, Entrepreneur, Creator — conviction multipliers)
       │
       ▼
   TradeSignal
  (signal_type, direction, entry/stop/target, conviction, risk_score)
       │
       ▼
   PaperTradingEngine
  (execute_signal → Trade)
       ├── CapitalGuard (drawdown limits, loss limits, kill switch → HALT)
       ├── CrashDetector v2 (6h/24h/72h multi-window drawdown velocity → PANIC)
       ├── DirectionController (rolling WR tracking → direction disable)
       ├── KnifeDetector (bounce quality, volume, momentum → falling_knife)
       ├── GapRiskEngine (overnight gap risk → stop cushion 1.0x-2.5x)
       └── SlippageEngine (spread model per asset → adjusted fills)
       │
       ▼
   PerformanceMemory
  (Trade attribution, agent track records, confidence calibration,
   per-asset/direction performance, opinion-outcome tracking)
       │
       ▼
   Monitoring
  (HealthMonitor — 10 checks: equity, guard, crash, positions, price data,
   cycle diversity, skips. Returns HEALTHY/DEGRADED/CRITICAL.)
       │
       ▼
   Telemetry
  (TelemetryRecorder — per-cycle JSONL, cumulative counters)
  (GuardAuditRecorder — guard intervention JSONL)
  (ExecutionAuditRecorder — execution block JSONL)
  (FailureClassifier — exception classification JSONL)
       │
       ▼
   Reporting
  (extended_demo_report.py — daily/weekly/reports from JSONL)
  (HealthMonitor console output per cycle)
```

## Major Modules

| Module | Location | Purpose |
|--------|----------|---------|
| CLI | `core/cli/main.py` | Entry point: collect, process, run, council, etc. |
| Config | `core/config/config.py` | Env-based configuration |
| EventBus | `core/event_bus/bus.py` | Decoupled pub/sub (12 topics, 1000 msg history) |
| Schemas | `core/schemas/` | Event, AgentOpinion, CouncilDecision, TradeSignal, Trade |
| Database | `core/database/db.py` | SQLite3 (events, opportunities, user_profiles) |
| Collectors | `core/collectors/` | WorldMonitorV2 orchestrates 7 collectors |
| Agents | `core/agents/` | News, Macro, Market (candidate-based), Risk, Trend |
| Council | `core/council/` | AgentCouncil v2 (weighted voting), MetaCouncil (3-profile) |
| Execution | `core/execution/` | PaperTrading, CrashDetector, CapitalGuard, DirectionController, KnifeDetector, GapRisk, Slippage, PerformanceMemory |
| Memory | `core/memory/` | ShortTermMemory (TTL), LongTermMemory (tagged) |
| Monitoring | `core/monitoring/` | HealthMonitor, Telemetry recorders, FailureClassifier |
| Profiles | `core/profiles/` | UserProfile, Trader/Entrepreneur/Creator pref models |
| Markets | `core/markets/` | Market profiles: crypto, forex, stocks, commodities, bonds, indices |
| Engines | `core/engines/` | ScoreEngine v1 (legacy), OpportunityEngine, Pipeline |

## Data Flow

```
External APIs → WorldMonitorV2 → EventBus → Agents → Council → MetaCouncil
  → PaperTradingEngine (with guard layers) → PerformanceMemory
  → OMACoreDatabase (SQLite) → Outputs
```

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
| `docs/data.json` | JSON | GitHub Pages export |

## Runtime Files

| File | Content |
|------|---------|
| `_extended_demo/run_state.json` | cycle_id, cumulative counters |
| `.env` | API keys (FRED, Telegram) |

## Audit Files

| File | Source | Content |
|------|--------|---------|
| `_project-memory/operational_validation/` | Sprint reports | Test reconciliation, architecture map, execution block audit, guard block audit, health audit, preflight, FLAW plans |
| `_project-memory/flaw_audit/` | Prior sprint | Flaw status matrix, fixed flaws verification, signal quality, stability, FLAW-21/24 reports |
| `_project-memory/ai_context/` | This system | Single source of truth for AI assistants |
