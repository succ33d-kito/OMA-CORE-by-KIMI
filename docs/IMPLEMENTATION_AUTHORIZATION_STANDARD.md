# Implementation Authorization Standard — O.M.A.-C.O.R.E.

**Status:** Canonical Engineering Governance

**Version:** 1.0

**Scope:** Mandatory authorization gate before any implementation

---

# 1. Purpose

The Implementation Authorization Standard defines the conditions under which implementation may proceed after Phase 3 of the Engineering Discovery Protocol.

Implementation Authorization answers: "Is implementation permitted?"

---

# 2. Authorization Principle

Implementation is authorized only if:

1. Architecture authorizes the capability.
2. Repository Discovery confirms the capability is not already certified.
3. Capability Gap Analysis identifies an actual implementation gap.
4. CAF dependencies are satisfied.
5. Engineering risks are acceptable.

Otherwise, implementation is forbidden.

---

# 3. Authorization Conditions

Every condition below must be satisfied for AUTHORIZED.

---

## Condition 1 — Architecture Authorization

The requested capability must be permitted by:

- ARCHITECTURE_V2.md
- PIPELINE_V2.md
- OBJECT_MODEL_V1.md
- ENGINEERING_CONSTITUTION.md
- All applicable ADRs

If the architecture explicitly forbids the capability, authorization is DENIED.

If the architecture is ambiguous about the capability, authorization is DEFERRED until escalation resolves the ambiguity.

---

## Condition 2 — Not Already Certified

Repository Discovery must confirm that no existing certified capability satisfies the request.

If a certified capability already covers the request, authorization is DENIED.

If a certified capability partially covers the request, authorization is AUTHORIZED_WITH_CONDITIONS and must explicitly exclude the already-certified portion.

---

## Condition 3 — Actual Implementation Gap

Capability Gap Analysis must classify the requested feature as:

- Missing
- Partially Implemented (gap portion only)

If classification is Already Implemented, Duplicate, Deprecated, or Conflicting, authorization is DENIED.

---

## Condition 4 — CAF Dependencies Satisfied

All capability dependencies must meet the required maturity level.

The recommended minimum for dependent development is Level 3 — Certified.

Lower maturity dependencies require an explicit Architecture Decision exception.

Dependency violations block authorization.

---

## Condition 5 — Engineering Risks Acceptable

The engineering risk assessment must conclude that:

- No critical risk blocks implementation.
- High risks have documented mitigation.
- Medium and low risks are acceptable.

---

# 4. Authorization Values

| Value | Meaning |
|---|---|
| AUTHORIZED | Implementation may proceed within the exact scope documented. |
| AUTHORIZED_WITH_CONDITIONS | Implementation may proceed but only within a reduced scope, with specific conditions documented. |
| NOT_AUTHORIZED | Implementation must not proceed. |

---

# 5. Authorization Decision Template

Every Implementation Authorization Decision must record:

| Field | Required Content |
|---|---|
| Sprint | Sprint identifier |
| Requested Capability | Capability ID and name |
| Architecture Authorization | PASS / FAIL — list governing documents and ADRs |
| Certification Check | PASS / FAIL — list existing certified capabilities reviewed |
| Gap Analysis Result | Gap classification and description |
| Dependency Check | PASS / FAIL — list dependencies and their maturity |
| Risk Assessment | Risk score and mitigation summary |
| Authorization Decision | AUTHORIZED / AUTHORIZED_WITH_CONDITIONS / NOT_AUTHORIZED |
| Conditions | If AUTHORIZED_WITH_CONDITIONS, list conditions |
| Escalation Required | YES / NO |
| Decision Date | Date of authorization |

---

# 6. Authorization Scope

When AUTHORIZED, implementation scope must:

- Match the authorized gap exactly.
- Exclude features classified as Already Implemented, Duplicate, or Deprecated.
- Not introduce functionality beyond the gap.
- Not modify forbidden modules.

---

# 7. Re-authorization

If the discovery context changes before or during implementation:

- If new contradictory evidence emerges, STOP implementation.
- Perform targeted re-discovery.
- Update the authorization decision.
- If NOT_AUTHORIZED, roll back changes.

---

# 8. Prohibited Actions

Without authorization, the following are prohibited:

- Writing implementation code.
- Creating new files in product modules.
- Modifying product modules.
- Adding new tests for unimplemented features.
- Creating new schemas.
- Creating new capabilities.
- Claiming a capability is under development.

Design-only work and architecture reading are permitted without authorization.
