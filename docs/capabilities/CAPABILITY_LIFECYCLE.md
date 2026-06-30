# Capability Lifecycle — CAF

**Status:** Canonical Capability Lifecycle Model

**Framework:** Capability Assurance Framework (CAF)

**Version:** 1.0

**Scope:** Governance documentation only

---

# 1. Purpose

This document defines the lifecycle states through which O.M.A.-C.O.R.E. capabilities move.

The lifecycle prevents premature implementation, premature certification, and silent retirement.

No transition may occur without evidence.

---

# 2. Canonical Lifecycle

```text
IDEA
↓
PROPOSED
↓
ARCHITECTED
↓
IMPLEMENTED
↓
DEMONSTRATED
↓
CERTIFIED
↓
OPERATIONAL
↓
TRUSTED
↓
DEPRECATED
↓
RETIRED
```

Not every capability must reach every later state.

No capability may skip the evidence required by a state transition.

---

# 3. Lifecycle vs Maturity

Lifecycle state and maturity level are related but not identical.

| Lifecycle State | Typical Maturity |
|---|---|
| IDEA | No maturity claim or Level 0 candidate |
| PROPOSED | Level 0 candidate |
| ARCHITECTED | Level 0 — Designed |
| IMPLEMENTED | Level 1 — Implemented |
| DEMONSTRATED | Level 2 — Demonstrated |
| CERTIFIED | Level 3 — Certified |
| OPERATIONAL | Level 4 — Operational |
| TRUSTED | Level 5 — Trusted |
| DEPRECATED | Maturity retained historically but not recommended for new dependencies |
| RETIRED | No longer active; dependency replacement required |

---

# 4. State Definitions and Transition Rules

## 4.1 IDEA

A concept exists but has not been formally proposed.

Entry evidence:

- note, discussion, or roadmap item.

Exit to PROPOSED requires:

- capability name;
- preliminary owner;
- problem or opportunity statement;
- rough dependency guess.

Forbidden:

- implementation;
- dependency by other capabilities;
- certification claims.

## 4.2 PROPOSED

A candidate capability has been formally proposed but not architected.

Entry evidence:

- proposal text;
- capability registry candidate;
- sprint candidate or ADR proposal if architectural.

Exit to ARCHITECTED requires:

- architecture or governance spec;
- owner confirmed;
- domain confirmed;
- dependencies identified;
- scope exclusions recorded;
- contradiction check completed.

Forbidden:

- product implementation unless the sprint explicitly moves to implementation after architecture acceptance;
- dependency by product capabilities unless design-only.

## 4.3 ARCHITECTED

The capability has a defined architecture or governance model.

Entry evidence:

- architecture document;
- accepted ADR;
- engineering review approving architecture;
- capability registry entry.

Exit to IMPLEMENTED requires:

- authorized sprint;
- test or evidence plan;
- dependency readiness;
- accepted scope;
- no contradiction with canonical documents.

Forbidden:

- claiming behaviour exists;
- treating design as certified capability.

## 4.4 IMPLEMENTED

The capability's scoped code or governance artifacts exist.

Entry evidence:

- files created or modified;
- implementation inventory;
- documentation inventory;
- architecture compliance check.

Exit to DEMONSTRATED requires:

- demonstration execution or governance application;
- observable output;
- traceability evidence;
- failure or risk evidence where applicable.

Forbidden:

- dependent development unless certification is not required and ADR exception exists.

## 4.5 DEMONSTRATED

The capability has been exercised successfully.

Entry evidence:

- test output;
- demonstration document;
- review output;
- deterministic demonstration when applicable.

Exit to CERTIFIED requires:

- full certification package;
- architecture verification;
- dependency analysis;
- risk assessment;
- regression result when code exists;
- accepted engineering review.

Forbidden:

- treating a single demonstration as operational trust.

## 4.6 CERTIFIED

The capability is certified for dependent development within its approved scope.

Entry evidence:

- certification decision;
- engineering review;
- capability demonstration if product behaviour exists;
- maturity update;
- metrics update.

Exit to OPERATIONAL requires:

- participation in end-to-end workflow;
- repeated stable use;
- operational audit evidence;
- incident handling rules.

Forbidden:

- expanding scope beyond what was certified;
- treating certification as live/autonomous approval.

## 4.7 OPERATIONAL

The capability participates in end-to-end workflows.

Entry evidence:

- repeated run evidence;
- workflow integration evidence;
- monitoring or audit results;
- operational stability record.

Exit to TRUSTED requires:

- historical trend evidence;
- stable dependency history;
- known failure modes;
- no unresolved high-risk debt.

Forbidden:

- treating operational status as permanent trust without audit.

## 4.8 TRUSTED

The capability is production-grade within its approved domain.

Entry evidence:

- longitudinal evidence;
- stability trend;
- incident trend;
- regression trend;
- audit history;
- dependency health trend.

Exit to DEPRECATED requires:

- replacement, risk, or architecture change evidence.

Forbidden:

- architecture bypass;
- unapproved autonomy increase;
- scope expansion without new certification.

## 4.9 DEPRECATED

The capability remains historically valid but should not be used for new dependencies.

Entry evidence:

- ADR or engineering review explaining deprecation;
- replacement path or containment plan.

Exit to RETIRED requires:

- no active dependencies or approved replacement;
- migration evidence;
- audit acceptance.

Forbidden:

- new dependent capabilities unless an ADR explicitly permits temporary use.

## 4.10 RETIRED

The capability is no longer active.

Entry evidence:

- retirement review;
- dependency migration complete;
- replacement recorded where applicable.

Forbidden:

- active dependency;
- operational use;
- certification claims for new work.

---

# 5. Transition Evidence Matrix

| Transition | Required Evidence |
|---|---|
| IDEA → PROPOSED | Proposal and preliminary ownership. |
| PROPOSED → ARCHITECTED | Architecture/specification and contradiction check. |
| ARCHITECTED → IMPLEMENTED | Authorized sprint and evidence plan. |
| IMPLEMENTED → DEMONSTRATED | Demonstration output or tests. |
| DEMONSTRATED → CERTIFIED | Certification package and accepted engineering review. |
| CERTIFIED → OPERATIONAL | Repeated workflow participation evidence. |
| OPERATIONAL → TRUSTED | Longitudinal stability and audit evidence. |
| TRUSTED → DEPRECATED | ADR or review documenting why replacement is needed. |
| DEPRECATED → RETIRED | Dependency migration and retirement review. |

---

# 6. Current Lifecycle Baseline

| Capability | Lifecycle State | Maturity |
|---|---|---|
| CAF-001 — Capability Assurance Framework | ARCHITECTED | Level 0 — Designed |
| EXEC-LIFECYCLE-001 — Execution Lifecycle | CERTIFIED | Level 3 — Certified |
| EXEC-ORDER-LEDGER-001 — Internal Order and Ledger Integrity | PROPOSED | Level 0 — Designed |
| EXEC-PORTFOLIO-001 — Virtual Position and Portfolio Consistency | IDEA | Level 0 — Designed |
| SCI-BRIDGE-001 — Scientific Bridge | ARCHITECTED | Level 0 — Designed |

---

# 7. Transition Governance

Every transition must update or reference:

- capability registry;
- capability maturity record;
- dependency record;
- engineering metrics when sprint-related;
- engineering review for implementation/certification transitions;
- ADR if architecture changes.

No silent transitions are permitted.
