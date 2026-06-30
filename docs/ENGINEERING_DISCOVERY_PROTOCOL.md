# Engineering Discovery Protocol — O.M.A.-C.O.R.E.

**Status:** Canonical Engineering Governance

**Version:** 1.0

**Scope:** Mandatory pre-implementation workflow

---

# 1. Purpose

The Engineering Discovery Protocol (EDP) establishes the mandatory pre-implementation workflow for every future O.M.A.-C.O.R.E. sprint.

No implementation may begin before EDP execution is complete and documented.

EDP exists to ensure that engineering decisions are based on the actual state of the repository rather than assumptions.

---

# 2. Engineering Principle

No engineer may implement a capability before answering three questions:

1. What does the architecture authorize?
2. What already exists in the repository?
3. What is the minimum change required to close the gap?

If any of these questions cannot be answered objectively, implementation must not begin.

---

# 3. Mandatory Pre-Implementation Phases

Every future implementation sprint shall execute the following phases in order.

---

## Phase 1 — Architecture Compliance Review

### Purpose

Determine which architecture documents govern the requested capability.

### Activities

1. Identify applicable canonical architecture documents.
2. Identify applicable Architecture Decisions (ADRs).
3. Identify applicable CAF entries and capability maturity records.
4. Identify capability dependencies and their certification status.
5. Identify all architectural constraints applicable to the sprint.

### Output

Architecture Compliance Report containing:

- applicable documents list;
- applicable ADRs with status;
- applicable CAF entries;
- dependency list with maturity status;
- architectural constraints;
- forbidden module list;
- contradiction check result (STOP if contradictions found).

### Contradiction Rule

If contradictions exist between architecture documents, implementation is STOPPED and must be escalated before proceeding.

---

## Phase 2 — Repository Capability Discovery

### Purpose

Inspect the repository to determine the current state of every artifact relevant to the requested capability.

### Activities

1. Identify existing implementations.
2. Identify existing packages.
3. Identify existing schemas.
4. Identify existing tests.
5. Identify existing certification status.
6. Identify existing engineering reviews.
7. Identify existing capability maturity.

### Output

Repository Discovery Report following `docs/REPOSITORY_DISCOVERY_STANDARD.md`.

### Restriction

No implementation decisions may be made during discovery.

---

## Phase 3 — Capability Gap Analysis

### Purpose

Compare the requested capability against the current repository state to determine what actually needs to be built.

### Activities

1. Classify each requested feature according to the gap classification standard.
2. Document the gap between requested and existing state.
3. Identify duplicate, conflicting, or deprecated artifacts.

### Output

Capability Gap Analysis following `docs/CAPABILITY_GAP_ANALYSIS_STANDARD.md`.

### Restriction

Each feature must be classified as exactly one gap type.

---

## Phase 4 — Implementation Authorization

### Purpose

Authorize implementation only for actual gaps that are architecturally permitted and not already certified.

### Activities

1. Verify architecture authorizes the capability.
2. Verify repository discovery confirms capability is not already certified.
3. Verify gap analysis identifies an actual implementation gap.
4. Verify CAF dependencies are satisfied.
5. Verify engineering risks are acceptable.

### Output

Implementation Authorization Decision following `docs/IMPLEMENTATION_AUTHORIZATION_STANDARD.md`.

Allowed values:

- AUTHORIZED
- AUTHORIZED_WITH_CONDITIONS
- NOT_AUTHORIZED

### Restriction

Existing certified capabilities must never be reimplemented. Duplicate implementations must be rejected.

---

## Phase 5 — Implementation

### Constraints

- Only authorized gaps may be implemented.
- Implementation scope must match the authorized gap exactly.
- No additional functionality may be introduced.
- No forbidden modules may be modified.

---

## Phase 6 — Certification

### Activities

After implementation completes:

1. Engineering Review.
2. Capability Demonstration.
3. CAF Update (registry, maturity, dependencies).
4. Engineering Metrics Update.
5. Readiness Decision.

---

# 4. Mandatory Reading Order

Before beginning Phase 1, the engineer must read the following documents in order:

1. ENGINEERING_MANIFESTO.md
2. ENGINEERING_CONSTITUTION.md
3. ARCHITECTURE_V2.md
4. PIPELINE_V2.md
5. OBJECT_MODEL_V1.md
6. IMPLEMENTATION_STRATEGY_V1.md
7. ARCHITECTURE_DECISIONS.md
8. ENGINEERING_METRICS.md
9. All CAF documents
10. All Engineering Reviews (Sprint 15A onward)

If contradictions exist during reading:

STOP.
Escalate.
Do not implement.

---

# 5. Deliverable Requirements

Each EDP execution must produce:

- Architecture Compliance Report (Phase 1)
- Repository Discovery Report (Phase 2)
- Capability Gap Analysis (Phase 3)
- Implementation Authorization Decision (Phase 4)

These documents become part of the sprint's engineering record.

---

# 6. Validation Requirements

The EDP is valid only if it:

- Prevents duplicate implementations.
- Detects existing certified capabilities.
- Prevents architecture bypass.
- Prevents speculative implementation.
- Produces deterministic implementation scope.

---

# 7. Final Principle

Understanding the system precedes changing the system.

Every implementation begins with discovery.

Every change begins with evidence.

Every capability is implemented only after its necessity has been objectively demonstrated.
