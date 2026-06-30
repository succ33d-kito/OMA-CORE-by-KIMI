# Capability Dependencies — CAF Standard

**Status:** Canonical Capability Dependency Policy

**Framework:** Capability Assurance Framework (CAF)

**Version:** 1.0

**Scope:** Governance documentation only

---

# 1. Purpose

This document defines how O.M.A.-C.O.R.E. capabilities may depend on one another.

Dependency governance prevents partial systems from becoming foundations for future work before they are mature enough to carry that responsibility.

---

# 2. Dependency Principle

A capability may depend only on capabilities with sufficient maturity.

Recommended minimum:

```text
Level 3 — Certified
```

A lower maturity dependency may be used only when:

- an Architecture Decision explicitly approves the exception;
- the dependent sprint documents the risk;
- the exception does not affect canonical object ownership;
- the dependency cannot introduce architecture drift;
- the exception has a defined containment plan.

---

# 3. Dependency Types

| Dependency Type | Meaning | Minimum Recommended Maturity |
|---|---|---|
| Architectural Dependency | Depends on a frozen architecture, ADR, or canonical specification. | Accepted / Canonical |
| Capability Dependency | Depends on another capability's behaviour or governance outcome. | Level 3 |
| Evidence Dependency | Depends on evidence produced by another sprint or capability. | Evidence accepted in review |
| Operational Dependency | Depends on a capability participating in an end-to-end workflow. | Level 4 |
| Trust Dependency | Depends on a capability being production-grade in its approved domain. | Level 5 |

---

# 4. Dependency Rules

- Dependencies must be explicit before implementation begins.
- A capability must not depend on an implicit side effect.
- A capability must not depend on unreviewed code.
- A capability must not depend on a proposed ADR unless the sprint explicitly remains design-only.
- A product capability should not depend on a Level 0, Level 1, or Level 2 capability.
- A governance capability may reference Level 0 future capabilities only as planned or proposed.
- Dependency maturity must be checked during engineering review.
- Dependency changes must be documented in the capability registry.
- Dependency violations block certification.

---

# 5. Forbidden Dependency Patterns

The following patterns are forbidden:

## 5.1 Circular capability dependency

Capability A requires Capability B while Capability B requires Capability A.

Result:

STOP and redesign sequencing through architecture review.

## 5.2 Upstream dependency on downstream learning

Operational or execution capabilities may not depend on Scientific Layer conclusions unless an approved future architecture defines the path.

This preserves:

- Approval authority;
- Execution ownership;
- Scientific downstream-only learning;
- AD-003.

## 5.3 Internal object leakage

A capability outside Execution Engine may not depend on internal Execution Engine objects such as ExecutionRequest unless a future read-only handoff contract explicitly authorizes it.

## 5.4 Premature external integration

No capability may depend on broker, Paper, Shadow, TradingView, or Live integration before internal execution evidence gates are satisfied and architecture approval exists.

## 5.5 Dependency on unaccepted proposals

A capability may not require AD-007 Hypothesis unless AD-007 is later accepted or superseded by a binding decision.

## 5.6 Dependency on implementation details

Capabilities may depend on certified behaviour and canonical contracts, not private implementation details.

## 5.7 Dependency on unstable operational side effects

Capabilities may not depend on incidental database rows, logs, CLI output, or runtime side effects unless those artifacts are explicitly defined as evidence or canonical outputs.

---

# 6. Dependency Graph Baseline

Current capability sequence from Implementation Strategy V1 and Sprint 15B evidence:

```text
Canonical Architecture Baseline
    ↓
Execution Engine Foundation
    ↓
EXEC-LIFECYCLE-001 — Execution Lifecycle
    ↓
EXEC.ORDER-LEDGER — Execution Memory
    ↓
EXEC.STATE — Execution State Certification
    ↓
OUTCOME.COLLECTOR — Outcome Collector
    ↓
SCI-BRIDGE-001 — Scientific Bridge
    ↓
Scientific Ingestion
    ↓
Criterion Generation
    ↓
Resource Loop
    ↓
External Integration Readiness Review
```

---

# 7. Current Dependency Status

| Capability | Depends On | Dependency Status | May Proceed? |
|---|---|---|---|
| EXEC-LIFECYCLE-001 | Execution Engine Foundation | Satisfied by Sprint 15A and Sprint 15B evidence | Already certified |
| EXEC.ORDER-LEDGER | EXEC-LIFECYCLE-001 Level 3 | Satisfied — EXEC-LIFECYCLE-001 is Level 3 Certified | Already certified |
| EXEC.STATE | EXEC-LIFECYCLE-001 Level 3; EXEC.ORDER-LEDGER Level 3 | Satisfied — both prerequisite capabilities are Level 3 Certified | Already certified |
| EXEC-SIMULATION-001 | EXEC-LIFECYCLE-001, EXEC.ORDER-LEDGER, EXEC.STATE | Satisfied for internal simulation readiness; not certified by Sprint 15E because Sprint 15E was explicitly scoped to Outcome Domain after AD-008 | Future sprint only if explicitly authorized |
| OUTCOME.COLLECTOR | EXEC-LIFECYCLE-001 Level 3; EXEC.ORDER-LEDGER Level 3; EXEC.STATE Level 3; AD-008 | Satisfied — prerequisites certified and Outcome Domain architecture accepted | Already certified |
| SCI-BRIDGE-001 | OUTCOME.COLLECTOR Level 3; Scientific Bridge Architecture V1 | Architecture exists; upstream Outcome capability now certified | Future sprint may begin if explicitly authorized |

---

# 8. Dependency Review Checklist

Before a sprint begins:

- [ ] Primary capability named.
- [ ] Capability owner identified.
- [ ] Required dependencies listed.
- [ ] Each dependency has maturity recorded.
- [ ] Dependencies meet Level 3 recommended minimum or have ADR exception.
- [ ] No circular dependency detected.
- [ ] No dependency on forbidden modules or external integration.
- [ ] No dependency on internal objects outside their owner boundary.
- [ ] No dependency on proposed ADRs unless sprint is design-only.
- [ ] Dependency risks documented.

Before certification:

- [ ] Dependency assumptions verified by tests, docs, or review evidence.
- [ ] Dependency graph updated if needed.
- [ ] Capability registry updated if status changed.
- [ ] Engineering review records dependency health.

---

# 9. Dependency Failure Handling

If a dependency is discovered to be immature or invalid:

1. Stop implementation or certification.
2. Record the dependency failure.
3. Determine whether the sprint can be reduced to design-only.
4. If not, keep the sprint open.
5. Create an ADR only if architecture must change.
6. Do not proceed by weakening the dependency rule.

---

# 10. Sprint 15C Readiness

Sprint 15C depends on:

```text
EXEC-LIFECYCLE-001 — Execution Lifecycle — Level 3 Certified
```

This dependency is satisfied.

CAF dependency policy therefore permits Sprint 15C to begin, provided Sprint 15C remains scoped to:

```text
ExecutionRequest → ExecutionOrder → ExecutionLedgerRecord
```

Sprint 15C must not introduce portfolio, positions, PnL, outcome, scientific ingestion, broker integration, external adapters, paper trading, or live trading.

---

# 11. Sprint 15D Certification Update

Sprint 15D depends on:

```text
EXEC-LIFECYCLE-001 — Execution Lifecycle — Level 3 Certified
EXEC.ORDER-LEDGER — Execution Memory — Level 3 Certified
```

These dependencies are satisfied.

Sprint 15D certified:

```text
EXEC.STATE — Execution State Certification — Level 3 Certified
```

The dependency graph now permits Sprint 15E to begin only within internal simulation readiness scope:

```text
Execution Lifecycle
↓
Execution Memory
↓
Execution State
↓
Internal End-to-End Simulation Validation
```

Sprint 15E remains blocked from outcome handoff, scientific ingestion, broker integration, external adapters, paper trading, live trading, and unapproved autonomy unless a future sprint order explicitly authorizes those capabilities.

---

# 12. Sprint 15E Certification Update

Sprint 15E depends on:

```text
EXEC-LIFECYCLE-001 — Execution Lifecycle — Level 3 Certified
EXEC.ORDER-LEDGER — Execution Memory — Level 3 Certified
EXEC.STATE — Execution State Certification — Level 3 Certified
AD-008 — Recognition of the Outcome Domain — ACCEPTED
```

These dependencies are satisfied.

Sprint 15E certified:

```text
OUTCOME.COLLECTOR — Outcome Collector — Level 3 Certified
```

The dependency graph now permits a future Sprint 15F only within an explicitly authorized downstream boundary such as:

```text
Outcome
↓
Scientific Bridge
↓
Evidence
```

Sprint 15F remains blocked from Knowledge generation, Criterion generation, broker integration, external adapters, Paper Trading, Shadow Mode, Live Mode, database persistence, CLI exposure, and unapproved autonomy unless a future sprint order explicitly authorizes those capabilities and canonical architecture permits them.
