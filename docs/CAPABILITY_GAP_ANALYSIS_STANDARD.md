# Capability Gap Analysis Standard — O.M.A.-C.O.R.E.

**Status:** Canonical Engineering Governance

**Version:** 1.0

**Scope:** Mandatory gap classification protocol

---

# 1. Purpose

The Capability Gap Analysis Standard defines how gaps between requested capabilities and current repository state are classified during Phase 3 of the Engineering Discovery Protocol.

Capability Gap Analysis answers: "What actually needs to be built?"

---

# 2. Gap Classification Principle

Each requested capability or feature must be classified as exactly one gap type.

No feature may receive multiple classifications.

No feature may remain unclassified.

---

# 3. Gap Classifications

---

## 3.1 Already Implemented

### Definition

The requested capability exists in the repository at the required maturity level.

### Examples

- An existing certified capability matches the requested capability.
- An existing certified capability satisfies the requested feature.
- An existing test suite validates the requested behaviour.

### Required Action

None. Document the existing capability as satisfying the request.

### Implementation Authorization

NOT_AUTHORIZED. Reimplementation is prohibited.

---

## 3.2 Partially Implemented

### Definition

The requested capability exists but does not meet the required maturity or scope.

### Examples

- Implementation exists at Level 1 but needs to reach Level 3.
- Implementation exists but excludes a required feature.
- Schema exists but transformation logic is missing.

### Required Action

Document the gap between current state and required state. Identify the specific missing features.

### Implementation Authorization

AUTHORIZED only for the documented gap. Existing implementation must not be reimplemented.

---

## 3.3 Missing

### Definition

The requested capability does not exist in the repository.

### Examples

- No package, schema, implementation, or test exists.
- The capability is documented as FUTURE or IDEA in the registry.
- No engineering review or capability demonstration exists.

### Required Action

Document the full scope of what must be implemented.

### Implementation Authorization

AUTHORIZED, subject to architecture compliance and dependency checks.

---

## 3.4 Duplicate

### Definition

The requested capability duplicates an existing capability that already serves the same architectural purpose.

### Examples

- Two capabilities with different names but identical purpose.
- A new feature request that matches an existing certified capability.
- An identical schema or object proposed under a different name.

### Required Action

Document the duplicate. Reference the existing capability.

### Implementation Authorization

NOT_AUTHORIZED. Duplicate implementations must be rejected.

---

## 3.5 Deprecated

### Definition

The requested capability was previously implemented but has been deprecated or superseded.

### Examples

- An ADR marks the capability as DEPRECATED.
- The capability was replaced by a newer capability.
- The capability is no longer aligned with current architecture.

### Required Action

Document the deprecation. Reference the replacement capability.

### Implementation Authorization

NOT_AUTHORIZED. Deprecated capabilities must not be reimplemented.

---

## 3.6 Conflicting

### Definition

The requested capability contradicts an existing architecture decision, certified capability, or canonical document.

### Examples

- Requested feature violates an accepted ADR.
- Requested feature would bypass Pipeline V2 flow.
- Requested feature would violate canonical ownership rules.
- Requested feature depends on a PROPOSED ADR as if accepted.
- Requested capability would create circular dependency.

### Required Action

Document the conflict. Identify the source of the contradiction.

### Implementation Authorization

NOT_AUTHORIZED. Conflicting implementations must be escalated through architecture review.

---

# 4. Classification Decision Flow

```
Requested Capability
    ↓
Does it already exist at required maturity?
    YES → Already Implemented → NOT_AUTHORIZED
    NO  → continue
    ↓
Does it exist at lower maturity?
    YES → Partially Implemented → AUTHORIZED for gap only
    NO  → continue
    ↓
Does the request duplicate an existing capability?
    YES → Duplicate → NOT_AUTHORIZED
    NO  → continue
    ↓
Is the requested capability deprecated?
    YES → Deprecated → NOT_AUTHORIZED
    NO  → continue
    ↓
Does the request conflict with architecture?
    YES → Conflicting → NOT_AUTHORIZED
    NO  → Missing → AUTHORIZED
```

---

# 5. Gap Analysis Report Template

Every Capability Gap Analysis Report must include:

| Section | Required Content |
|---|---|
| Sprint | Sprint identifier |
| Requested Capability | Capability ID and name |
| Gap Classification | One of the six classifications |
| Current State | What exists in the repository |
| Required State | What the capability must deliver |
| Gap Description | Specific features missing or conflicting |
| Existing References | Files, capabilities, ADRs, reviews that inform the classification |
| Risk Assessment | Risks of proceeding or not proceeding |
| Gap Verdict | AUTHORIZED / NOT_AUTHORIZED / ESCALATE |

---

# 6. Escalation Rules

If a capability is classified as Conflicting, or if classification is ambiguous:

1. STOP the implementation authorization process.
2. Document the ambiguity or conflict.
3. Escalate through the architecture decision process.
4. Do not proceed until the ambiguity is resolved.

---

# 7. Prohibited Actions

During gap analysis, the following are prohibited:

- Implementing any code.
- Redesigning the architecture to avoid a conflict.
- Reclassifying a Conflicting capability as Missing to bypass governance.
- Reclassifying an Already Implemented capability as Partially Implemented to justify reimplementation.
- Ignoring a Duplicate classification.
