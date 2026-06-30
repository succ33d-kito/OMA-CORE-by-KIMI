# Component Audit

## Summary table

| Component | Exists? | Operational status | Python files | Related tests | Risk |
|---|---|---|---|---|---|
| collectors | Yes | Experimental/partial | 12 | 2 | Medium |
| event_bus | Yes | Partial | 2 | 1 | Medium |
| agents | Yes | Partial | 6 | 5 | Low/Medium |
| council | Yes | Partial | 3 | 2 | Low/Medium |
| execution | Yes | Experimental/partial | 10 | 4 | Critical |
| execution_engine | Yes | Certified/isolated | 22 | 4 | Low/Medium |
| outcome_domain | Yes | Certified/isolated | 4 | 0 | Low/Medium |
| scientific | Yes | Experimental/partial | 13 | 1 | High |
| schemas | Yes | Partial | 9 | 2 | Low/Medium |
| database | Yes | Partial | 2 | 0 | High |
| monitoring | Yes | Partial | 4 | 0 | Medium |
| memory | Yes | Partial | 2 | 2 | Low/Medium |
| profiles | Yes | Partial | 2 | 1 | Low/Medium |
| markets | Yes | Partial | 9 | 2 | Low/Medium |
| cli | Yes | Experimental/partial | 2 | 0 | High |
| engines | Yes | Experimental/partial | 5 | 1 | Medium |
| processors | Yes | Partial | 1 | 0 | Low/Medium |


## Detailed findings

### Collectors
Exists under `core/collectors` with RSS, sentiment, Polymarket, FRED, Binance, CoinGecko, Yahoo, and world-monitor variants. Operational status is partial: unit tests cover selected collectors, but there is no proven unified collector reliability contract or source health registry.

### World Monitor
`world_monitor.py` and `world_monitor_v2.py` coexist. This is a duplicate/legacy signal: one should eventually be frozen, retired, or made explicit by governance.

### Schemas
`core/schemas` contains event, trade, agent, hypothesis, evidence, knowledge, criterion, and outcome comparison schemas. Several newer governed objects also live in `core/execution_engine/schemas` and `core/outcome_domain`. Schema duplication risk is high because canonical ownership is split across old and new domains.

### Event Bus
`core/event_bus/bus.py` exists and is tested. It appears in-process, not durable/distributed. Production eventing would require delivery guarantees, persistence, replay, and backpressure decisions.

### Agents
`core/agents` exists. Market/risk/news/macro/trend agents are heuristic components. Operationally useful for experimentation, but not production-certified.

### Council
`core/council` exists and is tested. It aggregates decisions but is not proven as a high-reliability decision governance service.

### Execution
Two execution worlds exist: legacy `core/execution` and governed `core/execution_engine`. This is the most important architectural duplication. Legacy execution contains paper trading and risk guards; new execution_engine is certified but not clearly integrated into the old runtime.

### Paper Trading
Present in legacy execution and script surfaces. It is experimental, tested, and explicitly not equivalent to production/live readiness.

### Risk
RiskAgent and guard modules exist, but risk enforcement is fragmented. A critical future task is to prove every execution path passes through the same risk gate.

### Monitoring
Health, telemetry, and failure classification exist. Production observability is incomplete: no durable metrics backend, alert SLO, or systematic operational dashboard contract is evident.

### Memory
Memory modules and performance memory exist. Growth, consistency, locking, and migration policies are not production-grade yet.

### Profiles
Profiles exist under `core/profiles` and are tested. Maturity is partial.

### Markets
Crypto, Forex, Stocks, Commodities, Indices, Bonds modules exist. Multi-market support is structural/experimental, not production-ready per market.

### CLI
The CLI exists but is a monolithic composition root. It imports database, collectors, scoring, notification, event bus, agents, council, scientific modules, config, and lifecycle functions at import/startup. This is operationally convenient but architecturally fragile.

### Database
SQLite database layer exists, with local DB files in repository. It is not production storage architecture. Postgres migration script exists but no proven migration/runbook is certified.

## Duplicate/dead/obsolete candidates

- `setup.py` is not packaging metadata; appears to embed/generated older project code.
- `world_monitor.py` vs `world_monitor_v2.py`.
- `core/execution` vs `core/execution_engine`.
- `OUTCOME_BRIDGE.md`/scientific outcome bridge code vs newly governed Outcome Domain and Scientific Bridge architecture.
- `__pycache__`, `.pytest_cache`, DBs, logs, score calibration generated reports are runtime/generated and should not be mixed with canonical source.
