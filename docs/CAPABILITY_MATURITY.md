# Capability Maturity — O.M.A.-C.O.R.E.

**Status:** Canonical Capability Maturity Registry

**Version:** 1.0

**Governance Scope:** Tracks maturity of certified engineering capabilities

---

# 1. Purpose

This document is the canonical capability maturity registry for O.M.A.-C.O.R.E.

It exists to make capability maturity explicit, measurable, and auditable across future sprints.

Capabilities are not mature because code exists.

Capabilities mature only when evidence demonstrates that their architectural contract works and that dependent development may safely proceed.

---

# 2. Capability Maturity Model

| Level | Name | Meaning |
|---|---|---|
| Level 0 | Designed | Architecture exists. No implementation. |
| Level 1 | Implemented | Code exists. No evidence yet. |
| Level 2 | Demonstrated | Capability has been executed successfully. Behaviour demonstrated. |
| Level 3 | Certified | Capability validated. Evidence collected. Architecture verified. Regression passed. Approved for dependent development. |
| Level 4 | Operational | Capability participates in end-to-end workflows. Stable under repeated execution. |
| Level 5 | Trusted | Capability has accumulated sufficient historical evidence. Considered production-grade. |

---

# 3. Governance Rules

- Capability entries are cumulative.
- Matured levels must be backed by evidence.
- Level changes are append-only in sprint reviews and reflected here as the current canonical maturity state.
- A capability cannot advance because implementation exists alone.
- Level 3 requires architecture verification and regression evidence.
- Level 4 requires participation in end-to-end workflows.
- Level 5 requires historical evidence over time.
- If evidence is later contradicted, maturity must be revised through an engineering review or architecture decision rather than historical rewriting.

---

# 4. Registry

| Capability | Owner | Current Level | Target Level | Evidence | Blocking Dependencies | Next Required Sprint |
|---|---|---|---|---|---|---|
| Execution Lifecycle | Execution Engine | Level 3 — Certified | Level 3 — Certified | Sprint 15B targeted tests: 7 passed; Sprint 15A+15B targeted tests: 11 passed; full regression: 876 passed, 3 warnings; architecture integrity tests passed; capability demonstration accepted | None for Sprint 15C entry; downstream work must preserve Sprint 15B boundaries | Sprint 15C — Orders and Ledger |

---

# 5. Execution Lifecycle Maturity History

## Initial entry

| Field | Value |
|---|---|
| Capability | Execution Lifecycle |
| Owner | Execution Engine |
| Initial Current Level | Level 0 — Designed |
| Target Level | Level 3 — Certified |
| Sprint | Sprint 15B |

## Certification update

| Field | Value |
|---|---|
| Capability | Execution Lifecycle |
| Owner | Execution Engine |
| Certified Level | Level 3 — Certified |
| Certification Sprint | Sprint 15B |
| Certification Evidence | `docs/CAPABILITY_DEMONSTRATION_15B.md`; `docs/SPRINT15B_ENGINEERING_REVIEW.md`; `tests/test_execution_lifecycle_15b.py`; full regression suite |
| Certification Decision | CERTIFIED |

---

# 6. Current Certification Meaning

Execution Lifecycle at Level 3 means:

- the minimal lifecycle has been implemented;
- the lifecycle has been demonstrated;
- deterministic behaviour has been tested;
- invalid inputs are rejected deterministically;
- traceability is preserved;
- architecture integrity has been verified;
- no forbidden dependencies were introduced;
- full regression passed;
- dependent work may proceed to Sprint 15C.

Execution Lifecycle at Level 3 does not mean:

- operational end-to-end execution exists;
- portfolio exists;
- positions exist;
- ledger integrity exists;
- outcome handoff exists;
- scientific ingestion exists;
- external integration is authorized;
- paper trading is authorized;
- live trading is authorized.

---

# 7. Next Maturity Boundary

The next possible maturity increase for Execution Lifecycle is Level 4 — Operational.

Level 4 is not authorized by Sprint 15B.

Level 4 requires the capability to participate in a broader end-to-end workflow after later capabilities are certified.

The next required dependent capability is:

Sprint 15C — Orders and Ledger
