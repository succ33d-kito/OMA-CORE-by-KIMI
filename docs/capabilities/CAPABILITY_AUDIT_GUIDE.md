# Capability Audit Guide — CAF

**Status:** Canonical Capability Audit Guide

**Framework:** Capability Assurance Framework (CAF)

**Version:** 1.0

**Scope:** Governance documentation only

---

# 1. Purpose

This document defines how O.M.A.-C.O.R.E. capabilities are audited.

Audits ensure that capabilities remain aligned with architecture, evidence, dependencies, risk, traceability, operational readiness, certification status, trust level, and engineering health.

An audit is not a redesign.

An audit observes, verifies, reports, and recommends.

---

# 2. Audit Principles

- Audit evidence must be objective.
- Audit findings must distinguish fact from recommendation.
- Audits must not rewrite historical records.
- Corrections require new review entries or ADRs.
- Audits must preserve architecture hierarchy.
- Audits must check both success and failure evidence.
- Audits must identify whether certification remains valid.

---

# 3. Audit Dimensions

CAF audits evaluate nine dimensions:

1. Architecture
2. Evidence
3. Dependencies
4. Risk
5. Traceability
6. Operational Readiness
7. Certification Status
8. Trust Level
9. Engineering Health

---

# 4. Architecture Audit

Purpose:

Verify that the capability still respects canonical architecture.

Checklist:

- [ ] Capability owner matches registry.
- [ ] Domain matches registry.
- [ ] No higher-priority architecture document is contradicted.
- [ ] Canonical object ownership is preserved.
- [ ] Internal objects have not leaked outside owner boundary.
- [ ] Pipeline flow is not bypassed.
- [ ] Forbidden modules remain untouched or explicitly authorized.
- [ ] Relevant ADRs are respected.
- [ ] Proposed ADRs are not treated as accepted.

Audit evidence:

- architecture docs;
- ADR registry;
- engineering review;
- code dependency scans if implementation exists;
- git diff/status when auditing recent work.

---

# 5. Evidence Audit

Purpose:

Verify that maturity and certification claims are supported by evidence.

Checklist:

- [ ] Engineering hypothesis exists.
- [ ] Demonstration evidence exists where required.
- [ ] Test evidence exists where code exists.
- [ ] Regression evidence exists where code exists.
- [ ] Failure behaviour evidence exists where relevant.
- [ ] Evidence is reproducible.
- [ ] Evidence references exact files, commands, or documents.
- [ ] Evidence is not merely a claim of intent.

Audit evidence:

- tests;
- command output;
- capability demonstrations;
- reviews;
- metrics;
- line counts for documentation-only governance artifacts.

---

# 6. Dependency Audit

Purpose:

Verify that dependency rules are satisfied and acyclic.

Checklist:

- [ ] All dependencies are listed.
- [ ] Dependency maturity levels are known.
- [ ] Recommended minimum Level 3 is met or ADR exception exists.
- [ ] No circular dependency exists.
- [ ] No dependency on proposed ADRs unless design-only.
- [ ] No dependency on forbidden modules.
- [ ] No dependency on implementation details outside capability ownership.
- [ ] Dependency risks are documented.

Audit evidence:

- capability dependency document;
- capability registry;
- maturity records;
- import/dependency scans when code exists;
- engineering review dependency analysis.

---

# 7. Risk Audit

Purpose:

Verify that risks are known, ranked, and contained.

Checklist:

- [ ] Critical risks listed or explicitly none.
- [ ] High risks listed or explicitly none.
- [ ] Medium risks listed or explicitly none.
- [ ] Low risks listed or explicitly none.
- [ ] Residual risk documented.
- [ ] Mitigation plan exists for non-zero risks.
- [ ] Risk score aligns with engineering metrics.
- [ ] Risk does not block dependent development.

Audit evidence:

- engineering review risk section;
- engineering metrics;
- incident reports if operational;
- ADRs for accepted risk.

---

# 8. Traceability Audit

Purpose:

Verify that identifiers, ownership, and evidence remain traceable.

Checklist:

- [ ] Required identifiers are preserved.
- [ ] No identifier is regenerated improperly.
- [ ] Input-to-output trace is documented.
- [ ] Creator and owner are explicit.
- [ ] Consumers are explicit.
- [ ] Trace is preserved in demonstrations or tests.
- [ ] Error paths preserve traceability where possible.
- [ ] Historical reviews can reconstruct why maturity changed.

Audit evidence:

- capability demonstration;
- tests;
- object ownership tables;
- engineering review;
- ADRs.

---

# 9. Operational Readiness Audit

Purpose:

Determine whether a capability may participate in operational workflows.

Checklist:

- [ ] Capability is at least Level 3 before dependent development.
- [ ] Capability is at least Level 4 before being called operational.
- [ ] Failure modes are documented.
- [ ] Rollback or containment exists where applicable.
- [ ] Monitoring or audit mechanism exists for operational use.
- [ ] Dependency chain is mature enough.
- [ ] No live/autonomous expansion is implied by readiness.

Audit evidence:

- operational run evidence;
- repeated execution evidence;
- monitoring reports;
- incident reviews;
- dependency maturity records.

---

# 10. Certification Status Audit

Purpose:

Verify whether certification remains valid.

Checklist:

- [ ] Certification decision exists.
- [ ] Certification scope is clear.
- [ ] Current usage does not exceed certified scope.
- [ ] Certification criteria were satisfied.
- [ ] New evidence has not contradicted certification.
- [ ] Maturity registry matches certification status.
- [ ] Engineering metrics match certification status.

Audit outcomes:

| Outcome | Meaning |
|---|---|
| Certification Valid | Current evidence supports certification. |
| Certification Conditional | Certification remains valid but requires monitoring. |
| Certification At Risk | New evidence may invalidate certification. |
| Certification Revocation Recommended | Certification no longer supported. |

---

# 11. Trust Level Audit

Purpose:

Determine whether the capability has enough historical evidence for Level 5 trust.

Checklist:

- [ ] Capability is operational first.
- [ ] Historical evidence spans multiple runs or periods.
- [ ] Regression trend is stable.
- [ ] Incident trend is acceptable.
- [ ] Dependency trend is stable.
- [ ] Architecture drift remains absent.
- [ ] Known failure modes are controlled.
- [ ] No unresolved high-risk technical debt exists.

Trust cannot be granted from a single sprint.

---

# 12. Engineering Health Audit

Purpose:

Evaluate whether the capability improves or harms long-term engineering health.

Checklist:

- [ ] Architecture compliance remains PASS.
- [ ] Evidence quality is sufficient.
- [ ] Technical debt is absent or controlled.
- [ ] Dependencies remain valid.
- [ ] Documentation is complete.
- [ ] Regression remains healthy.
- [ ] Risk score is acceptable.
- [ ] Engineering health score is stable or improving.
- [ ] Capability improves one-person maintainability.

Audit evidence:

- engineering metrics;
- sprint review;
- dependency record;
- test/regression output;
- technical debt report.

---

# 13. Standard Capability Audit Checklist

Use this checklist for every capability audit.

## Identity

- [ ] Capability ID is registered.
- [ ] Name is stable.
- [ ] Owner is explicit.
- [ ] Domain is explicit.
- [ ] Description matches current scope.

## Maturity

- [ ] Current maturity level recorded.
- [ ] Level evidence exists.
- [ ] Maturity claim does not exceed evidence.
- [ ] Level transition history exists.

## Lifecycle

- [ ] Current lifecycle state recorded.
- [ ] Transition evidence exists.
- [ ] No silent transition occurred.

## Architecture

- [ ] Canonical docs respected.
- [ ] ADRs respected.
- [ ] Ownership preserved.
- [ ] No forbidden boundaries crossed.

## Dependencies

- [ ] Dependencies listed.
- [ ] Dependency maturity sufficient.
- [ ] No circular dependency.
- [ ] No forbidden dependency pattern.

## Evidence

- [ ] Hypothesis or governance purpose exists.
- [ ] Demonstration/review evidence exists.
- [ ] Tests exist when code exists.
- [ ] Regression exists when code exists.
- [ ] Failure behaviour evidence exists when relevant.

## Risk and Debt

- [ ] Risk score assigned.
- [ ] Risk mitigations documented.
- [ ] Technical debt status documented.
- [ ] Blocking debt absent or explicitly escalated.

## Certification

- [ ] Certification status recorded.
- [ ] Certification decision valid for current scope.
- [ ] Engineering review accepted.
- [ ] Metrics updated.

## Recommendation

- [ ] Continue as-is.
- [ ] Continue with monitoring.
- [ ] Block dependent work.
- [ ] Require ADR.
- [ ] Recommend deprecation.
- [ ] Recommend retirement.

---

# 14. Audit Report Template

Every audit report should include:

| Section | Required Content |
|---|---|
| Capability | ID, name, owner, domain. |
| Audit Scope | What was audited and why. |
| Evidence Reviewed | Files, tests, reviews, metrics, ADRs. |
| Architecture Findings | Compliance and drift findings. |
| Dependency Findings | Dependency maturity and cycle findings. |
| Traceability Findings | Identifier and ownership findings. |
| Risk Findings | Risk score and residual risks. |
| Certification Findings | Whether certification remains valid. |
| Trust Findings | Whether operational/trusted claims are supported. |
| Recommendations | Proceed, monitor, block, ADR, deprecate, retire. |
| Final Audit Verdict | PASS, PASS_WITH_MONITORING, FAIL, ESCALATE. |

---

# 15. Sprint 15C Pre-Audit Recommendation

Before Sprint 15C begins, audit:

```text
EXEC-LIFECYCLE-001 — Execution Lifecycle
```

Expected audit result based on current evidence:

```text
PASS
```

Reason:

- Capability is Level 3 Certified.
- Dependency for Sprint 15C is satisfied.
- Architecture and dependency evidence exists.
- Regression passed in Sprint 15B.

Sprint 15C must still perform its own fresh prerequisite check before implementation.
