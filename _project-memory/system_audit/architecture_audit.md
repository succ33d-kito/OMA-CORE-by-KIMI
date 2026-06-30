# Architecture Audit

## Canonical architecture observed

The repository contains both canonical governance documents and implementation code. The most current governed architecture separates:

```text
Source → Collector → Validation → Event → Event Bus → Agents → Council → Execution → Outcome Domain → Scientific Bridge → Scientific Layer → Reports/CLI/User
```

Risk, Monitoring, Memory, and Learning exist as partially separate subsystems rather than one fully integrated production runtime.

## Layer-by-layer audit

| Layer | Purpose | Outputs | Dependencies | Maturity | Debt/Missing pieces | Risk |
|---|---|---|---|---|---|---|
| Source | External feeds/APIs/files | Raw news/market/macro data | Collectors, scripts | Available but heterogeneous | No source reliability registry; network clients spread across collectors/scripts | Medium |
| Collector | Fetch external data | Event-like records | requests, yfinance, feedparser, binance/FRED adapters | Partial | Mixed collector styles; legacy world_monitor and world_monitor_v2 coexist | Medium |
| Validation | Normalize/guard inputs | Validated Event/TradeSignal data | schemas, yahoo_data_guard, tests | Partial | No single validation gateway for all inputs | High |
| Event | UniversalEvent/Event dataclasses | Event objects and DB rows | core.schemas.event_schema, event_bus | Partial | Multiple event/schema concepts; generated setup.py duplication | Medium |
| Event Bus | Topic publish/subscribe | In-process event dispatch | core.event_bus.bus | Tested unit component | No distributed durability/backpressure | Medium |
| Agents | News/Macro/Market/Risk/Trend reasoning | Agent signals | core.agents, schemas.agent_schema | Partial | Heuristic scoring; inconsistent live data assumptions | High |
| Council | Aggregate agent votes/decisions | CouncilDecision | core.council | Partial/tested | Not proven under live multi-agent stress | High |
| Execution | Legacy execution, guards, paper trading | Trade execution simulation artifacts | core.execution | Experimental | Legacy execution coexists with new certified execution_engine; production boundary unclear | Critical |
| Execution Engine | Governed internal execution lifecycle/memory/state | ExecutionResult and internal records | core.execution_engine | Level 3 certified through 15D in docs/tests | Untracked in git; not integrated with legacy runtime | Medium |
| Outcome Domain | Outcome Collector | Outcome | core.outcome_domain | Level 3 certified in current working tree/tests | Very new; untracked; not integrated into CLI/runtime | Medium |
| Risk | RiskAgent, CapitalGuard, crash/knife/gap guards | Risk flags and limits | core.agents.risk_agent, core.execution.* | Partial | No single enforced risk gate across all execution paths | Critical |
| Monitoring | Health, telemetry, failure classifier | Health/telemetry objects | core.monitoring | Partial/tested | No production observability backend or alert routing guarantee | High |
| Memory | PerformanceMemory and memory store | Historical records | core.memory, core.execution.performance_memory | Partial | File/SQLite growth and consistency need operational policy | Medium |
| Learning | Scientific layer candidates/extractors | Evidence/Knowledge/Criterion | core.scientific | Experimental/partially implemented | Architecture docs say some future boundaries; code already exists and may predate governance | High |
| Reports | Docs, audit scripts, summaries | Markdown/JSON outputs | docs, scripts, _project-memory | Active | Generated reports mixed with source tree; retention unclear | Medium |
| CLI | User command surface | Console commands, DB mutations, exports | core.cli.main | Large/functional but high-risk | 1115-line god CLI initializes many dependencies at startup | High |


## Architecture conclusion

Architecture documentation is ahead of runtime integration quality. The strongest engineering asset is the emerging governance/CAF discipline and the new certified isolated domains. The weakest architecture point is coexistence of older legacy execution/scientific paths with newer governed domains without a single authoritative runtime composition root.
