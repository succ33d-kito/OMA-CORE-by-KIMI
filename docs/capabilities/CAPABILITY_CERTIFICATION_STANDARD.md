# Capability Certification Standard — CAF

**Status:** Canonical Certification Standard

**Framework:** Capability Assurance Framework (CAF)

**Version:** 1.0

**Scope:** Governance documentation only

---

# 1. Purpose

This document defines the standard process for certifying O.M.A.-C.O.R.E. capabilities.

Certification means a capability is trustworthy enough for dependent development within its approved scope.

Certification does not mean operational, autonomous, production-grade, or live-capital-ready unless the capability scope and architecture explicitly say so.

---

# 2. Certification Principle

A capability may be certified only when evidence proves:

- architecture is preserved;
- ownership is preserved;
- dependency rules are satisfied;
- behaviour or governance purpose is demonstrated;
- risks are known;
- technical debt is declared;
- regression status is acceptable when code exists;
- certification decision is recorded.

No evidence, no certification.

---

# 3. Required Certification Package

Every capability certification must include:

1. Engineering Hypothesis
2. Evidence
3. Architecture Compliance
4. Dependency Analysis
5. Regression Results
6. Risk Assessment
7. Technical Debt
8. Engineering Review
9. Certification Decision
10. Required Sign-offs

---

# 4. Engineering Hypothesis

Every certification begins with one primary hypothesis.

The hypothesis must state:

- what capability is being certified;
- what behaviour or governance outcome must be demonstrated;
- which boundaries must be preserved;
- what uncertainty is reduced.

A sprint with multiple independent hypotheses must be split unless explicitly approved as a governance-only review.

---

# 5. Evidence

Evidence must be objective.

Accepted evidence includes:

- tests and test output;
- demonstrations;
- architecture integrity scans;
- dependency analysis;
- line counts for documentation deliverables;
- git status showing scope;
- audit reports;
- accepted engineering reviews;
- accepted capability demonstrations;
- regression output.

Unacceptable evidence includes:

- intent;
- confidence without output;
- code existence alone;
- undocumented assumptions;
- unreviewed logs;
- undocumented manual inspection;
- claims without reproducible artifacts.

---

# 6. Architecture Compliance

Certification must verify compliance with applicable canonical documents.

At minimum, product capability certification must check:

- Engineering Manifesto;
- Engineering Constitution;
- Architecture V2;
- Pipeline V2 where object flow is affected;
- Object Model V1 where canonical objects are affected;
- Integration Architecture where execution is affected;
- Scientific Bridge Architecture where outcome/evidence handoff is affected;
- Implementation Strategy V1;
- Architecture Decisions;
- Engineering Metrics;
- current Capability Registry and Dependency rules.

Architecture compliance must explicitly state:

- preserved boundaries;
- untouched forbidden modules;
- canonical ownership status;
- whether any ADR is required.

---

# 7. Dependency Analysis

Certification must include:

- dependency graph;
- allowed dependencies;
- forbidden dependencies checked;
- maturity of prerequisite capabilities;
- circular dependency check;
- internal object leakage check;
- proposed ADR dependency check.

A dependency violation blocks certification.

---

# 8. Regression Results

When code exists, regression results are mandatory.

At minimum:

- targeted capability tests;
- relevant prior sprint tests;
- full repository regression suite unless impossible;
- compile or syntax verification where applicable;
- warning interpretation.

If full regression cannot run, the engineering review must document:

- why;
- what alternative evidence was used;
- whether certification is blocked or conditional.

---

# 9. Risk Assessment

Certification risk assessment must include:

- critical risks;
- high risks;
- medium risks;
- low risks;
- residual risks;
- mitigation plan;
- whether risk blocks dependent development.

Risk score must align with `docs/ENGINEERING_METRICS.md`:

| Score | Meaning |
|---|---|
| 0 | No known governance risk. |
| 1 | Low risk, contained and documented. |
| 2 | Medium risk requiring monitoring. |
| 3 | High risk requiring mitigation before dependent work. |
| 4 | Critical risk; sprint should not proceed or should be halted. |

---

# 10. Technical Debt

Certification must declare technical debt status.

Allowed outcomes:

- none intentionally introduced;
- known debt documented and non-blocking;
- blocking debt found, certification denied;
- debt accepted by explicit ADR.

Undocumented debt blocks certification.

---

# 11. Engineering Review

Every certification must produce or reference an engineering review.

The review must include:

- Sprint Information;
- Engineering Hypothesis;
- Capability Delivered;
- Architecture Compliance;
- Evidence;
- Dependency Analysis;
- Risk Analysis;
- Technical Debt;
- Lessons Learned;
- Engineering Metrics;
- Readiness Assessment;
- Architecture Decisions;
- Recommendations;
- Definition of Done Verification;
- Final Engineering Verdict.

This preserves the Sprint 15A/15B review standard.

---

# 12. Certification Decision

Allowed certification decisions:

| Decision | Meaning |
|---|---|
| CERTIFIED | Capability satisfies certification criteria. |
| CERTIFIED_WITH_CONDITIONS | Capability satisfies criteria but has explicit non-blocking conditions. Requires monitoring. |
| NOT_CERTIFIED | Capability failed certification. Dependent work blocked. |
| DEFERRED | Evidence insufficient or contradiction unresolved. |
| REVOKED | Prior certification invalidated by new evidence. |

A Level 3 maturity update requires `CERTIFIED` or an explicitly justified `CERTIFIED_WITH_CONDITIONS`.

---

# 13. Required Sign-offs

For a one-person engineering system, sign-offs are roles, not necessarily separate people.

Required sign-offs:

| Sign-off | Responsibility |
|---|---|
| Architecture Sign-off | Confirms no architecture drift, contradiction, or ownership violation. |
| Capability Sign-off | Confirms capability hypothesis was satisfied. |
| Evidence Sign-off | Confirms evidence is objective and reproducible. |
| Dependency Sign-off | Confirms dependencies are mature enough and acyclic. |
| Risk Sign-off | Confirms risk is documented and acceptable. |
| Readiness Sign-off | Confirms whether dependent work may begin. |

If the same human performs all sign-offs, the engineering review must still list each sign-off explicitly.

---

# 14. Certification Gate

A capability reaches Level 3 only if all checks pass:

- [ ] Engineering hypothesis satisfied.
- [ ] Evidence produced.
- [ ] Architecture preserved.
- [ ] Ownership preserved.
- [ ] Dependencies valid.
- [ ] No circular dependencies.
- [ ] No forbidden dependency patterns.
- [ ] Regression passed or documented non-code exception applies.
- [ ] Risk acceptable.
- [ ] Technical debt acceptable.
- [ ] Engineering review accepted.
- [ ] Certification decision recorded.
- [ ] Capability registry updated.
- [ ] Maturity registry updated.
- [ ] Metrics updated.

---

# 15. Sprint 15B Reference Certification

Sprint 15B is the reference product certification example:

| Field | Value |
|---|---|
| Capability | EXEC-LIFECYCLE-001 — Execution Lifecycle |
| Certification Decision | CERTIFIED |
| Maturity | Level 3 — Certified |
| Evidence | `docs/SPRINT15B_ENGINEERING_REVIEW.md`, `docs/CAPABILITY_DEMONSTRATION_15B.md`, `tests/test_execution_lifecycle_15b.py`, full regression result |
| Readiness | READY_FOR_15C |

Future capability certifications should meet or exceed the quality of the Sprint 15B evidence package.
