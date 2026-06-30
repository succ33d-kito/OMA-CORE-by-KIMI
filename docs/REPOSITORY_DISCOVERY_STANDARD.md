# Repository Discovery Standard — O.M.A.-C.O.R.E.

**Status:** Canonical Engineering Governance

**Version:** 1.0

**Scope:** Mandatory repository inspection protocol

---

# 1. Purpose

The Repository Discovery Standard defines how engineers inspect the repository during Phase 2 of the Engineering Discovery Protocol.

Repository Discovery answers: "What already exists?"

---

# 2. Discovery Principle

No implementation decisions may be made during discovery.

Discovery observes, catalogs, and reports.

It does not evaluate, prioritize, or authorize.

---

# 3. Required Discovery Dimensions

Every repository discovery must inspect the following dimensions.

---

## 3.1 Capability Identity

For each capability relevant to the sprint:

- Capability ID.
- Name.
- Owner.
- Domain.
- Registry status.

Source: `docs/capabilities/CAPABILITY_REGISTRY.md`

---

## 3.2 Repository Location

For each relevant capability:

- Package path.
- Module path.
- Schema path.
- Test path.
- Documentation path.

---

## 3.3 Certification Status

For each relevant capability:

- Current lifecycle state (IDEA → RETIRED).
- Current maturity level (0–5).
- Certification decision (CERTIFIED / NOT_CERTIFIED / etc.).
- Certification date and sprint.

Source: `docs/capabilities/CAPABILITY_REGISTRY.md`, `docs/CAPABILITY_MATURITY.md`, `docs/ENGINEERING_METRICS.md`

---

## 3.4 Engineering Review

For each relevant capability:

- Most recent engineering review.
- Engineering hypothesis validated or pending.
- Evidence summary.
- Readiness decision.

Source: `docs/SPRINT*_ENGINEERING_REVIEW.md` files.

---

## 3.5 Test Coverage

For each relevant capability:

- Test file location.
- Number of tests.
- Test categories (unit, integration, architecture, failure).
- Test runner output (pass/fail count).
- Full regression status.

---

## 3.6 Capability Maturity

For each relevant capability:

- Current maturity level.
- Level history.
- Blocking dependencies preventing advancement.

Source: `docs/CAPABILITY_MATURITY.md`, `docs/capabilities/CAPABILITY_MATURITY.md`

---

## 3.7 Dependencies

For each relevant capability:

- List of dependencies.
- Dependency maturity levels.
- Dependency certification status.
- Dependency chain health.

Source: `docs/capabilities/CAPABILITY_DEPENDENCIES.md`

---

## 3.8 Related ADRs

For each relevant capability:

- ADRs that govern the capability.
- ADR status (ACCEPTED / PROPOSED / etc.).
- Whether any ADR blocks the intended work.

Source: `docs/ARCHITECTURE_DECISIONS.md`

---

# 4. Discovery Methods

Accepted discovery methods:

- Reading canonical architecture documents.
- Reading engineering reviews.
- Reading capability registry and maturity records.
- Reading CAF documents.
- Reading ADR registry.
- Reading engineering metrics.
- Inspecting file trees.
- Inspecting module imports.
- Inspecting test files.
- Running targeted discovery commands (grep, import scans, file listings).
- Running regression tests to determine current health.

---

# 5. Discovery Report Template

Every Repository Discovery Report must include:

| Section | Required Content |
|---|---|
| Sprint | Sprint identifier |
| Requested Capability | Capability ID and name |
| Discovery Date | Date of inspection |
| Documents Read | List of all documents read |
| Packages Found | Relevant packages and paths |
| Schemas Found | Relevant schemas and paths |
| Tests Found | Relevant test files and test counts |
| Certification Status | Current lifecycle and maturity for each relevant capability |
| Engineering Reviews | Most recent review and readiness decision |
| Dependency Status | Dependency maturity and health |
| Related ADRs | ADRs governing the capability |
| Discovery Verdict | CAPABILITY_EXISTS / CAPABILITY_PARTIAL / CAPABILITY_MISSING / DUPLICATE_FOUND / CONFLICT_FOUND |

---

# 6. Prohibited Actions

During discovery, the following are prohibited:

- Making implementation decisions.
- Evaluating whether implementation should proceed.
- Prioritizing features.
- Redesigning architecture.
- Writing implementation code.
- Modifying product files.
- Creating new capabilities.

Discovery is observation. Nothing more.
