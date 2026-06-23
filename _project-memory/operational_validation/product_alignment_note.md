# Product Alignment Note

Generated: 2026-06-23

## Operational Validation — Current Phase

The Extended Demo is the current operational validation phase. It is divided into three stages:

| Stage | Duration | Command | Status |
|-------|----------|---------|--------|
| 7-day smoke run | 7 days | `python scripts/extended_demo_realtime.py --smoke` | ✅ READY |
| 30-day validation run | 30 days | `python scripts/extended_demo_realtime.py --run` | ⏳ PENDING (needs smoke pass) |
| 90-day extended demo | 90 days | `python scripts/extended_demo_realtime.py --extended` | ⏳ PENDING (needs 30d pass) |

The purpose of operational validation is to verify:
- Operational stability (no crashes, no guard failures)
- Monitoring completeness (no silent failures)
- Telemetry accuracy (counters match audit records)
- Reporting clarity (all states explainable)
- Gate criteria met (17 GO criteria for Extended Demo)

## Capital Status

| Stage | Status | Rationale |
|-------|--------|-----------|
| **Micro Capital** | 🚫 **NO-GO** | Extended Demo 30-day run must complete and pass Gate first |
| **Real Capital** | 🚫 **NO-GO** | Micro Capital must complete first |
| **Forex Activation** | 🚫 **NO-GO** | Real Capital must be stable first |

None of these stages are active. The system operates exclusively in paper/demo mode. No real funds are at risk.

## Product Direction

### Current OSIRIS Core Pipeline

```
Event → Agent Opinions → Council Decision → TradeSignal → PaperTrading
```

This is the current pipeline as implemented. Events flow from WorldMonitorV2 through the agent swarm, council, and into paper trading with full guard protection.

### Future O.M.A.-C.O.R.E. Product Layer

```
Event → Opportunity → User Profile → Action
```

The future product vision transforms from a single-purpose trading system to a multi-profile intelligence engine:

- **Event**: Same as today — external signals from APIs, news, market data
- **Opportunity**: A scored, typed, risk-weighted abstraction (already partially implemented in ScoreEngine/OpportunityEngine v1)
- **User Profile**: Persona-based evaluation (Trader, Entrepreneur, Creator) — MetaCouncil prototype exists
- **Action**: Profile-dependent actions — trade, invest, start business, create content

### What This Means

The current OSIRIS trading pipeline (Event → Agent → Council → TradeSignal → PaperTrading) is the **first concrete instantiation** of the broader O.M.A.-C.O.R.E. vision. The MetaCouncil and three-profile models already glimpse the future direction.

**The Opportunity Layer is NOT implemented.** Do not build it. Do not plan for it. The immediate focus remains on making the current trading pipeline observable, auditable, and operationally safe through the Extended Demo.

### Separation of Concerns

| Layer | Status | Responsibility |
|-------|--------|----------------|
| OSIRIS Core (current) | ✅ ACTIVE | Trading pipeline: Event → Agent → Council → Signal → PaperTrading |
| OSIRIS Operational Validation | 🔄 IN PROGRESS | Extended Demo: 7d smoke → 30d run → Gate → (future) Micro Capital |
| O.M.A.-C.O.R.E. Product Layer | 📋 FUTURE | Opportunity → User Profile → Action (not yet implemented) |

The product layer is documented here for architectural awareness only. No code changes are required or permitted.
