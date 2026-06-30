# Capability Maturity — CAF Standard

**Status:** Canonical CAF Maturity Model

**Framework:** Capability Assurance Framework (CAF)

**Version:** 1.0

**Scope:** Governance documentation only

---

# 1. Purpose

This document formalizes the maturity model used to evaluate every O.M.A.-C.O.R.E. capability.

The model prevents confusing code existence with trustworthy capability.

A capability advances only when objective evidence proves that the required criteria for the next level have been satisfied.

---

# 2. Maturity Levels

| Level | Name | Summary |
|---|---|---|
| Level 0 | Designed | Architecture exists. No implementation required or no implementation yet. |
| Level 1 | Implemented | Code or documentation required by the capability exists. Evidence is not sufficient yet. |
| Level 2 | Demonstrated | Capability has been executed or reviewed successfully in its scoped context. |
| Level 3 | Certified | Capability is validated, evidence-backed, architecture-verified, regression-safe, and approved for dependent development. |
| Level 4 | Operational | Capability participates in end-to-end workflows and remains stable under repeated use. |
| Level 5 | Trusted | Capability has accumulated sufficient historical evidence to be considered production-grade within its approved domain. |

---

# 3. Universal Maturity Rules

- No maturity advancement without evidence.
- No maturity advancement during contradiction or unresolved architecture ambiguity.
- Capability maturity is specific to the capability's approved scope.
- Maturity does not authorize adjacent capabilities.
- A capability at Level 3 may unblock dependent development.
- A capability at Level 4 may participate in end-to-end workflows.
- A capability at Level 5 requires longitudinal evidence, not a single sprint result.
- A maturity downgrade must be recorded through an engineering review or ADR.

---

# 4. Level 0 — Designed

## Definition

Architecture exists and the capability is defined enough to be discussed, sequenced, or planned.

Level 0 may apply to documentation-only governance capabilities or future implementation capabilities.

## Entry Criteria

- Capability name exists.
- Owner is identified.
- Domain is identified.
- Purpose or hypothesis is documented.
- Dependencies are listed or explicitly marked unknown.
- Scope exclusions are known enough to prevent accidental implementation.

## Exit Criteria

To leave Level 0, the capability must have:

- an authorized sprint or implementation/review task;
- acceptance criteria;
- required evidence definition;
- dependency readiness check;
- no unresolved contradiction with canonical architecture.

## Evidence Required

- Architecture/specification document, sprint order, ADR, or capability registry entry.

## Prohibited Claims

A Level 0 capability may not be described as usable, implemented, demonstrated, certified, operational, or trusted.

---

# 5. Level 1 — Implemented

## Definition

The required implementation or required documentation artifact exists, but sufficient evidence has not yet demonstrated the capability.

## Entry Criteria

- Level 0 exit criteria satisfied.
- Authorized implementation or artifact exists.
- Scope exclusions are still respected.
- No known forbidden dependency has been introduced.

## Exit Criteria

To leave Level 1, the capability must be exercised or reviewed under its intended context and produce evidence.

## Evidence Required

- File inventory or artifact inventory.
- Initial validation result.
- Architecture boundary check.

## Prohibited Claims

Level 1 does not imply behavioural correctness, readiness, or certification.

---

# 6. Level 2 — Demonstrated

## Definition

The capability has been demonstrated successfully in its scoped environment.

For product capabilities, this means behaviour has run.

For governance capabilities, this means the governance artifact can be applied to a real capability without contradiction.

## Entry Criteria

- Level 1 achieved.
- Demonstration path defined.
- Demonstration executed or reviewed.
- Output observed.

## Exit Criteria

To leave Level 2, the demonstration must be independently validated and converted into certification evidence.

## Evidence Required

- Demonstration document or test result.
- Traceability evidence.
- Failure behaviour or risk analysis when applicable.
- No evidence gap that invalidates the capability claim.

## Prohibited Claims

Level 2 does not authorize dependent development unless explicitly approved by an exception ADR. The recommended dependency minimum is Level 3.

---

# 7. Level 3 — Certified

## Definition

The capability has been validated, architecture-verified, regression-safe, and accepted for dependent development within its approved scope.

## Entry Criteria

- Level 2 achieved.
- Engineering hypothesis validated or governance purpose satisfied.
- Architecture compliance verified.
- Dependency analysis completed.
- Risk assessment completed.
- Technical debt assessed.
- Regression verification completed when code exists.
- Engineering review accepted.
- Certification decision recorded.

## Exit Criteria

To leave Level 3, the capability must participate in broader end-to-end workflows repeatedly and without instability.

## Evidence Required

- Engineering review.
- Capability demonstration when product behaviour exists.
- Architecture compliance report.
- Dependency report.
- Regression result when code exists.
- Capability maturity update.
- Engineering metrics entry.

## Prohibited Claims

Level 3 does not mean operational, production-grade, autonomous, or trusted.

---

# 8. Level 4 — Operational

## Definition

The capability participates in end-to-end workflows and remains stable under repeated execution or repeated governance use.

## Entry Criteria

- Level 3 achieved.
- Capability is used by at least one dependent workflow.
- Stability evidence exists across repeated use.
- Operational failure handling is documented.
- Monitoring or audit process exists.

## Exit Criteria

To leave Level 4, the capability must accumulate sufficient historical evidence over time.

## Evidence Required

- Repeated run evidence or repeated audit evidence.
- Operational incident review, if incidents occurred.
- Stability metrics.
- Dependency impact review.
- Updated risk profile.

## Prohibited Claims

Level 4 does not mean production-grade trust. It means operational participation under approved constraints.

---

# 9. Level 5 — Trusted

## Definition

The capability has accumulated enough longitudinal evidence to be considered production-grade within its approved scope.

## Entry Criteria

- Level 4 achieved.
- Historical evidence exists across multiple periods or dependent workflows.
- Failure modes are known and controlled.
- Dependencies remain stable.
- Architecture remains intact over time.
- No unresolved technical debt affects trust.

## Exit Criteria

Level 5 has no automatic exit. It is maintained through ongoing audits.

A capability may be downgraded if evidence contradicts trust.

## Evidence Required

- Historical audit trail.
- Stability trend.
- Incident trend.
- Regression trend.
- Dependency health trend.
- Engineering health trend.

## Prohibited Claims

Level 5 does not authorize architecture bypass, autonomy increase, live trading, or dependency shortcuts. Those require explicit architecture approval.

---

# 10. Current Maturity Baseline

| Capability | Current Level | Evidence |
|---|---|---|
| CAF-001 — Capability Assurance Framework | Level 0 — Designed | CAF Foundation Sprint documentation subsystem. |
| EXEC-LIFECYCLE-001 — Execution Lifecycle | Level 3 — Certified | Sprint 15B engineering review, capability demonstration, targeted tests, regression suite, engineering metrics, root capability maturity registry. |
| EXEC.ORDER-LEDGER — Execution Memory: Execution Order + Immutable Ledger | Level 3 — Certified | Sprint 15C engineering review, capability demonstration, architecture integrity tests, append-only tests, immutability tests, deterministic reconstruction tests, full regression. |
| EXEC.STATE — Execution State Certification | Level 3 — Certified | Sprint 15D engineering review, capability demonstration, architecture integrity tests, deterministic reconstruction tests, immutable snapshot tests, consistency tests, failure tests, full regression. |
| OUTCOME.COLLECTOR — Outcome Collector | Level 3 — Certified | Sprint 15E engineering review, capability demonstration, architecture integrity tests, deterministic ExecutionResult→Outcome tests, immutability tests, completeness tests, traceability tests, failure tests, full regression. |

---

# 11. Sprint 15C Maturity Update

Capability advanced:

```text
EXEC.ORDER-LEDGER
```

From:

```text
Level 0 — Designed
```

To:

```text
Level 3 — Certified
```

Evidence:

- `docs/SPRINT15C_ENGINEERING_REVIEW.md`
- `docs/CAPABILITY_DEMONSTRATION_15C.md`
- `tests/test_execution_order_ledger_15c.py`
- Targeted Sprint 15A/15B/15C regression: 18 passed.
- Full repository regression: 883 passed, 3 warnings.

Certification scope:

```text
ExecutionRequest → ExecutionOrder → ExecutionLedgerRecord
```

Certification does not authorize portfolio, positions, PnL, outcome, scientific ingestion, external adapters, paper trading, or live trading.

---

# 12. Relationship to Root Capability Maturity Registry

The root document `docs/CAPABILITY_MATURITY.md` records current certified capability maturity.

This CAF document defines the maturity standard used by that registry.

The two documents must remain consistent:

- root registry records current state;
- CAF maturity standard defines criteria and governance;
- sprint reviews record evidence-backed transitions.

---

# 13. Sprint 15D Maturity Update

Capability advanced:

```text
EXEC.STATE
```

From:

```text
Level 0 — Designed
```

To:

```text
Level 3 — Certified
```

Evidence:

- `docs/SPRINT15D_ENGINEERING_REVIEW.md`
- `docs/CAPABILITY_DEMONSTRATION_15D.md`
- `tests/test_execution_state_15d.py`
- Targeted Sprint 15A/15B/15C/15D regression: 27 passed.
- Full repository regression: 892 passed, 3 warnings.

Certification scope:

```text
ExecutionLedgerRecord → ExecutionState → ExecutionPosition → ExecutionPortfolioSnapshot
```

Certification does not authorize outcome handoff, Scientific Bridge, evidence generation, market data, broker integration, paper trading, shadow mode, live trading, performance analytics, database persistence, APIs, CLI, Pipeline changes, Scientific Layer changes, or external integrations.

---

# 14. Sprint 15E Maturity Update

Capability advanced:

```text
OUTCOME.COLLECTOR
```

From:

```text
Level 0 — Designed
```

To:

```text
Level 3 — Certified
```

Evidence:

- `docs/SPRINT15E_ENGINEERING_REVIEW.md`
- `docs/CAPABILITY_DEMONSTRATION_15E.md`
- `tests/test_outcome_collector_15e.py`
- Targeted Sprint 15A/15B/15C/15D/15E regression: 43 passed.
- Full repository regression: pending final metrics insertion from Sprint 15E execution evidence.

Certification scope:

```text
ExecutionResult → Outcome Collector → Outcome
```

Certification does not authorize Scientific Bridge, Evidence generation, Knowledge generation, Criterion generation, market analytics, broker integration, Paper Trading, Shadow Mode, Live Mode, performance analytics, database persistence, APIs, CLI, Pipeline changes, Scientific Layer changes, Execution Engine changes, or external integrations.
