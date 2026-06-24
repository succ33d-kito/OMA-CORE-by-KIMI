# OSIRIS / O.M.A.-C.O.R.E. — MASTER CONTEXT

*Last updated: 2026-06-23 23:00 UTC*

---

## PROJECT IDENTITY

**O.M.A.-C.O.R.E.** (One Man Army — Cosmic OSIRIS Intelligence Engine) v2.1.0.
Vision: From global events to intelligent action — a multi-profile decision engine for Trader, Entrepreneur, and Creator personas.

---

## CURRENT STATE

| Metric | Value |
|--------|-------|
| **Phase** | Extended Demo — 7-Day Smoke Run |
| **Smoke Run** | 🟢 RUNNING (cycle 3/672, started 2026-06-23 22:27 UTC) |
| **Tests** | 277 passed, 4 skipped (network-dep), 0 failed |
| **Branch** | main (`0135683`) |
| **Capital** | Micro/Real/Forex all 🚫 NO-GO |
| **Validation** | Operational validation ✅ complete |

---

## PIPELINE (simplified)

```
WorldMonitorV2 → EventBus → Agents → AgentCouncil → MetaCouncil
  → TradeSignal → PaperTradingEngine (guarded) → PerformanceMemory
  → Monitoring → Telemetry → Reports
```

Guards: CapitalGuard, CrashDetector v2 (6h/24h/72h), DirectionController, KnifeDetector, GapRiskEngine, SlippageEngine.

---

## ACTIVE PRIORITIES

1. 🟢 **7-Day Smoke Run** — ACTIVE (cycles every 15min)
2. ❌ **FLAW-25** — Guard audit records show `guard_source: "Unknown"`, `block_reason: "unknown"` — 6 records affected
3. ❌ **FLAW-24** — `crash_detector.summary()` hardcodes equity=10000 (reporting only, trade safety OK)
4. 🔶 **FLAW-21** — `Trade.close()` lacks idempotency guard (low risk, no practical exploit)
5-10. 📋 Future phases (Opportunity Layer, Profiles, Dashboard, Micro Capital, Real Capital)

---

## OPEN FLAWS

| ID | Risk | Summary |
|----|------|---------|
| FLAW-21 | LOW | Trade.close() idempotency (defense-in-depth) |
| FLAW-24 | LOW | CrashDetector summary() equity hardcoded |
| FLAW-25 | MEDIUM | Guard audit attribution: Unknown source/reason |

---

## SMOKE RUN STATUS (latest cycle)

- Cycles: 3 | Events: 6 | Signals: 0 | Trades: 0 | Errors: 0
- Guard blocks: 6 | Exec blocks: 0 | Equity: $10,000
- Guard mode: normal | Crash mode: none
- Health: all 10 checks HEALTHY

---

## COMPLETED MILESTONES

- **FLAW-14** ✅ Candidate-based signal selection (13 tests), RSI<30 BUY restored
- **FLAW-16** ✅ Multi-window CrashDetector (21 tests), COVID/FTX/LUNA replay passes
- **FLAW-17** ✅ KnifeDetector tests (11 tests)
- **FLAW-18** ✅ Kill switch tests (9 tests), HALT confirmed
- **Monitoring** ✅ HealthMonitor, TelemetryRecorder, GuardAuditRecorder, ExecutionAuditRecorder, FailureClassifier
- **Harness** ✅ `extended_demo_realtime.py` + `extended_demo_report.py`
- **Validation** ✅ Tests reconciled, architecture mapped, execution/guard/health audited, preflight passed (20/20 → GO)

---

## CONSTRAINTS (DO NOT VIOLATE)

- NO changes to MarketAgent, RiskAgent, AgentCouncil, PaperTradingEngine, CapitalGuard, CrashDetector, KnifeDetector, GapRiskEngine, DirectionController, SlippageEngine, PerformanceMemory
- NO trading/signal/risk/execution/portfolio logic changes
- NO new agents, indicators, collectors, dashboards, databases, broker integrations
- NO PnL/return/Sharpe optimization
- ALLOWED: monitoring, telemetry, reporting, audit scripts, tests, documentation, .gitignore

---

## AI WORKFLOW RULES

1. **Read `project_state.md`** before acting
2. **Repository state overrides AI memory** — verify claims against files
3. **Update `architecture.md`** when architecture changes
4. **Update `future_roadmap.md`** when roadmap changes
5. **Update `open_flaws.md`** when flaws are fixed or reclassified
6. **Update `completed_work.md` + `project_state.md`** after every major sprint

---

## FILES IN THIS SYSTEM

```
_project-memory/ai_context/
├── project_state.md          ← READ THIS FIRST
├── architecture.md
├── current_priorities.md
├── completed_work.md
├── open_flaws.md
├── operational_status.md
├── future_roadmap.md
├── ai_workflow.md
├── MASTER_CONTEXT.md          ← This file
└── context_system_report.md
```

## NEXT STEP

Monitor the active 7-day smoke run. If it completes without NO-GO triggers:
`python scripts/extended_demo_report.py` then `python scripts/extended_demo_realtime.py --run`
