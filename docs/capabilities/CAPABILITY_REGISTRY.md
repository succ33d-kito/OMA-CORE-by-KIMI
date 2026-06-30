# Capability Registry — O.M.A.-C.O.R.E.

**Status:** Canonical Capability Identity Registry

**Framework:** Capability Assurance Framework (CAF)

**Version:** 1.0

**Scope:** Governance documentation only

---

# 1. Purpose

This document defines the canonical identity of capabilities in O.M.A.-C.O.R.E.

A capability is a certifiable unit of engineering value that preserves architecture, produces evidence, and enables dependent development.

A capability is not:

- a feature;
- a file;
- a module;
- a code volume target;
- an implementation convenience;
- a speculative abstraction.

The registry exists so future work can answer:

- What capability exists?
- Who owns it?
- What domain does it belong to?
- What evidence certifies it?
- What depends on it?
- Which reviews and ADRs govern it?

---

# 2. Governance Rules

- Capability identities are canonical once accepted.
- Capability records are append-only.
- Historical certification records are never rewritten.
- Corrections are introduced through a later engineering review or ADR.
- A capability may not be treated as available unless its maturity and dependency requirements are satisfied.
- A capability may not be split, merged, or renamed without an Architecture Decision.
- Implementation work must reference the capability it advances.
- Every future sprint must name exactly one primary capability.

---

# 3. Required Capability Record Fields

Every capability record must include:

| Field | Required Meaning |
|---|---|
| Capability ID | Stable canonical identifier. |
| Name | Human-readable capability name. |
| Owner | Canonical subsystem or layer that owns the capability. |
| Domain | Architectural domain where the capability belongs. |
| Description | What the capability makes possible. |
| Current Status | Lifecycle status under CAF. |
| Current Maturity | Capability maturity level. |
| Dependencies | Capabilities required before this one may be implemented or used. |
| Engineering Reviews | Sprint or governance reviews that evaluated this capability. |
| Certification History | Evidence-backed maturity changes. |
| Related ADRs | Architecture decisions governing the capability. |

---

# 4. Canonical Capability Domains

| Domain | Scope |
|---|---|
| Architecture Governance | Canonical specs, ADRs, metrics, CAF, review standards. |
| Execution Engine | Internal execution lifecycle, orders, ledger, portfolio, positions, execution results. |
| Outcome Domain | Outcome creation, validation, completeness, publication readiness, ownership, and lifecycle. |
| Scientific Bridge | Outcome-to-Evidence translation boundary. |
| Scientific Layer | Evidence, knowledge, validation, future hypothesis review, criterion learning. |
| Pipeline | Canonical object flow and ownership boundaries. |
| Operational Flow | Collectors, events, council, approval, operational guards. |
| Strategic Resource Flow | CriterionDelta, ResourceState, scarce resource reasoning. |
| Integration | Future optional external connectivity after internal capability evidence exists. |

---

# 5. Registry

## CAF-001 — Capability Assurance Framework

| Field | Value |
|---|---|
| Capability ID | CAF-001 |
| Name | Capability Assurance Framework |
| Owner | Engineering Governance |
| Domain | Architecture Governance |
| Description | Defines how O.M.A.-C.O.R.E. capabilities are identified, matured, certified, audited, and governed. |
| Current Status | ARCHITECTED |
| Current Maturity | Level 0 — Designed |
| Dependencies | Engineering Manifesto, Engineering Constitution, Architecture V2, Implementation Strategy V1, Architecture Decisions, Engineering Metrics, Capability Maturity, Sprint 15B review and demonstration evidence. |
| Engineering Reviews | CAF Foundation Sprint — this documentation subsystem. |
| Certification History | Designed during CAF Foundation Sprint; not a product capability and not execution-certified. |
| Related ADRs | AD-004 canonical ownership rule; AD-005 Sprint 15A validated; future ADR recommended if CAF becomes a top-level governance authority document. |

## EXEC-LIFECYCLE-001 — Execution Lifecycle

| Field | Value |
|---|---|
| Capability ID | EXEC-LIFECYCLE-001 |
| Name | Execution Lifecycle |
| Owner | Execution Engine |
| Domain | Execution Engine |
| Description | Transforms a canonical ExecutionSignal into a canonical ExecutionResult through an internal ExecutionRequest while preserving deterministic behaviour, traceability, ownership, isolation, and zero operational side effects. |
| Current Status | CERTIFIED |
| Current Maturity | Level 3 — Certified |
| Dependencies | Execution Engine Foundation / Capability 02; Architecture Governance baseline; AD-001; AD-002; AD-004; AD-005. |
| Engineering Reviews | `docs/SPRINT15B_ENGINEERING_REVIEW.md` |
| Certification History | Certified in Sprint 15B with targeted tests, failure tests, architecture integrity tests, compile verification, and full regression. |
| Related ADRs | AD-001; AD-002; AD-004; AD-005. |

## EXEC.ORDER-LEDGER — Execution Memory: Execution Order + Immutable Ledger

| Field | Value |
|---|---|
| Capability ID | EXEC.ORDER-LEDGER |
| Previous Planning ID | EXEC-ORDER-LEDGER-001 |
| Name | Execution Memory — Execution Order + Immutable Ledger |
| Owner | Execution Engine |
| Domain | Execution Engine |
| Description | Certified capability that makes internal execution operations reconstructible through ExecutionOrder lifecycle and append-only immutable ExecutionLedgerRecord behavior. |
| Current Status | CERTIFIED |
| Current Maturity | Level 3 — Certified |
| Dependencies | EXEC-LIFECYCLE-001 at Level 3 minimum. |
| Engineering Reviews | `docs/SPRINT15C_ENGINEERING_REVIEW.md` |
| Certification History | Certified in Sprint 15C with architecture integrity tests, request→order→ledger behavior tests, append-only tests, immutability tests, deterministic reconstruction tests, compile verification, and full regression. |
| Related ADRs | AD-001; AD-002; AD-004; AD-005. |

## EXEC.STATE — Execution State Certification

| Field | Value |
|---|---|
| Capability ID | EXEC.STATE |
| Previous Planning ID | EXEC-PORTFOLIO-001 |
| Name | Execution State Certification |
| Owner | Execution Engine |
| Domain | Execution Engine |
| Description | Certified capability that reconstructs the authoritative internal operational state from immutable ExecutionLedgerRecord history through ExecutionState, ExecutionPosition, and immutable portfolio snapshots. |
| Current Status | CERTIFIED |
| Current Maturity | Level 3 — Certified |
| Dependencies | EXEC-LIFECYCLE-001 at Level 3 minimum; EXEC.ORDER-LEDGER at Level 3 minimum. |
| Engineering Reviews | `docs/SPRINT15D_ENGINEERING_REVIEW.md` |
| Certification History | Certified in Sprint 15D with architecture integrity tests, ledger→state→position→snapshot tests, deterministic reconstruction tests, immutable snapshot tests, consistency tests, failure tests, compile verification, and full regression. |
| Related ADRs | AD-001; AD-004. |

## EXEC-SIMULATION-001 — Internal End-to-End Simulation Validation

| Field | Value |
|---|---|
| Capability ID | EXEC-SIMULATION-001 |
| Name | Internal End-to-End Simulation Validation |
| Owner | Execution Engine |
| Domain | Execution Engine |
| Description | Future capability to validate internal Engine execution from ExecutionSignal through ExecutionResult using orders, positions, portfolio snapshots, and ledger evidence in SIMULATION mode. |
| Current Status | IDEA |
| Current Maturity | Level 0 — Designed |
| Dependencies | EXEC-LIFECYCLE-001; EXEC.ORDER-LEDGER; EXEC.STATE. All must reach Level 3 minimum before operational use. |
| Engineering Reviews | None yet. Candidate for Sprint 15E. |
| Certification History | None yet. |
| Related ADRs | AD-001; AD-002; AD-004; AD-005. |

## OUTCOME.COLLECTOR — Outcome Collector

| Field | Value |
|---|---|
| Capability ID | OUTCOME.COLLECTOR |
| Previous Planning ID | OUTCOME-HANDOFF-001 |
| Name | Outcome Collector |
| Owner | Outcome Collector |
| Domain | Outcome Domain |
| Description | Certified capability that transforms a certified ExecutionResult into a canonical immutable Outcome while preserving factual integrity, deterministic behaviour, complete traceability, ownership, and Outcome Domain isolation. |
| Current Status | CERTIFIED |
| Current Maturity | Level 3 — Certified |
| Dependencies | EXEC-LIFECYCLE-001 at Level 3 minimum; EXEC.ORDER-LEDGER at Level 3 minimum; EXEC.STATE at Level 3 minimum; AD-008 Outcome Domain architecture. |
| Engineering Reviews | `docs/SPRINT15E_ENGINEERING_REVIEW.md` |
| Certification History | Certified in Sprint 15E with architecture integrity tests, ExecutionResult→Outcome deterministic transformation tests, immutability tests, completeness tests, traceability tests, failure tests, compile verification, import-boundary scan, and regression verification. |
| Related ADRs | AD-003; AD-004; AD-008; Outcome Architecture V1; Scientific Bridge Architecture V1. |

## SCI-BRIDGE-001 — Scientific Bridge

| Field | Value |
|---|---|
| Capability ID | SCI-BRIDGE-001 |
| Name | Scientific Bridge |
| Owner | Scientific Bridge |
| Domain | Scientific Bridge |
| Description | Future capability to transform validated operational Outcome into scientific Evidence without modifying operational, outcome, or scientific domains. |
| Current Status | ARCHITECTED |
| Current Maturity | Level 0 — Designed |
| Dependencies | OUTCOME.COLLECTOR Level 3; Outcome stability; Scientific Bridge Architecture V1. |
| Engineering Reviews | Scientific Bridge Architecture V1 architecture refinement. |
| Certification History | Architecture defined; no implementation or certification yet. |
| Related ADRs | AD-003; AD-004; AD-007 remains proposed and not accepted. |

---

# 6. Registry Maintenance Rules

A future capability may be added only when it has:

- a clear owner;
- a clear domain;
- explicit dependencies;
- a capability hypothesis or purpose;
- a maturity target;
- a planned review artifact;
- no circular dependency with existing capabilities.

A capability may advance in maturity only when evidence is recorded in:

- an engineering review;
- a capability demonstration when applicable;
- engineering metrics;
- capability maturity registry;
- dependency registry when dependency status changes.

---

# 7. Current Governance Interpretation

O.M.A.-C.O.R.E. currently has four certified product capabilities:

```text
EXEC-LIFECYCLE-001 — Execution Lifecycle — Level 3 Certified
EXEC.ORDER-LEDGER — Execution Memory — Level 3 Certified
EXEC.STATE — Execution State — Level 3 Certified
OUTCOME.COLLECTOR — Outcome Collector — Level 3 Certified
```

The next capability may begin only when explicitly scoped by a future mission order and its prerequisites are certified. The likely next downstream candidate is:

```text
SCI-BRIDGE-001 — Scientific Bridge
```

CAF itself is governance infrastructure. It does not certify product functionality and does not modify the Execution Engine.
