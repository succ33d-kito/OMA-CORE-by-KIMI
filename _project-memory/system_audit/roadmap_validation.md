# Roadmap Validation

## Evidence reviewed

- Canonical architecture docs.
- Sprint 13/15 engineering reports.
- Capability registry/maturity/dependencies.
- Existing scientific docs and reports.
- Source tree and tests.

## Completed

- Baseline collector/event/scoring/CLI experimentation.
- Execution Engine foundation/lifecycle/memory/state certifications in working tree.
- Outcome Domain recognition and Outcome Collector certification in working tree.
- Scientific layer exploratory modules and tests exist.

## Obsolete or needs quarantine

- Treat `setup.py` bootstrap/generated code as obsolete until proven otherwise.
- Treat unguided legacy execution expansion as frozen until reconciled with `core/execution_engine`.
- Treat pre-governance scientific outcome bridge flows as experimental until re-certified under Scientific Bridge architecture.

## Still valid

- CAF certification path.
- Architecture-first sprint governance.
- Outcome → Scientific Bridge → Evidence → Knowledge → Criterion sequence.
- Need for internal simulation/paper/live gates, but only after ownership boundaries are settled.

## Wrong priority risks

- Building more trading strategy before runtime/risk/execution authority is clarified.
- Adding more collectors before source governance and validation are unified.
- Expanding scientific learning before canonical Evidence bridge is certified.

## New 90-day roadmap

### Days 1–30: Stabilize and freeze

1. Freeze live/paper/execution expansion.
2. Clean repository hygiene: remove pycache, DBs, logs, secrets from source tracking.
3. Create architecture index mapping each module to domain owner.
4. Decide legacy `core/execution` vs governed `core/execution_engine` migration path.
5. Add dependency lockfile, secret scanning, Bandit/pip-audit.

### Days 31–60: Certify integration spine

1. Certify Scientific Bridge only: Outcome → Evidence.
2. Build full canonical integration test without live trading.
3. Define single mandatory risk gate.
4. Define runtime envelope: queue, replay, failure handling, telemetry.
5. Establish DB migration and artifact retention policy.

### Days 61–90: Operational hardening

1. Reconcile CLI into modular commands.
2. Add soak/stress/restart tests.
3. Certify paper trading only after risk/execution authority is unified.
4. Add market-by-market readiness gates.
5. Produce production readiness gate checklist and block live trading until every gate passes.
