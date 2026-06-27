# Innovation Lanes

*Version 1.0 — June 2026*

---

## Lane Overview

Ideas are classified into four lanes based on their risk profile, operational impact, and implementation readiness. The lane determines review depth, implementation sequence, and safety constraints.

| Lane | Color | Risk Level | Implementation | Review Depth |
|------|-------|------------|----------------|--------------|
| **GREEN** | 🟢 | Very low to low | Can be implemented now on USB | Light |
| **YELLOW** | 🟡 | Low to medium | Valuable but premature | Standard |
| **ORANGE** | 🟠 | Medium to high | Needs research or design review | Deep |
| **RED** | 🔴 | High to very high | Must wait until evidence exists | Maximum |

---

## GREEN — Safe Implementation

### Definition

Additive, low-risk ideas that improve observability, documentation, analytics, reporting, or tooling. GREEN ideas do not touch the execution path, decision-making logic, or operational databases.

### Entry Criteria

- Does not modify any existing operational code path
- Does not affect trade execution, Council decisions, agent opinions, or collector behavior
- Does not write to `oma_core.db`
- Does not require changes to existing tests
- Can be implemented entirely on USB with no integration dependency on the laptop version
- Improves at least one scarce resource or removes technical debt

### Exit Criteria

- Implemented and validated on USB
- Tests pass
- Documentation updated
- Review confirms no scope creep into YELLOW/ORANGE/RED territory

### Examples

- Missed Opportunity Ledger
- Notification Quality Gate
- Signal-to-Decision Audit
- Terminal Cockpit Evolution
- Documentation improvements
- Test coverage improvements
- Monitoring and observability additions

### Required Review Depth

Light — all 14 review questions answered concisely. Self-review sufficient.

---

## YELLOW — Strategic Backlog

### Definition

Aligned, valuable ideas that are premature due to missing dependencies, insufficient evidence, or unfavorable timing. YELLOW ideas should be implemented eventually — just not yet.

### Entry Criteria

- Aligned with Architecture V2
- Would clearly improve Criterion, decision quality, or scarce resources
- Cannot be implemented now because:
  - A dependency does not exist yet
  - The system lacks sufficient data to validate it
  - A higher-priority item must come first
  - The idea is not yet specific enough to design

### Exit Criteria

- Dependencies are met
- Evidence exists that it is now the right time
- Risk assessment is favorable
- Re-reviewed and promoted to GREEN or returned to backlog

### Examples

- Decision DNA (requires 100+ hypothesis-linked decisions)
- Criterion Timeline (requires CriterionSnapshot)
- Confidence Calibration (requires 100+ decision records)

### Required Review Depth

Standard — full answers to all 14 questions. Project lead review.

---

## ORANGE — Research / Architecture Risk

### Definition

Ideas that may affect the architecture, require significant design work, or depend on unresolved research questions. ORANGE ideas need investigation before implementation can be evaluated.

### Entry Criteria

- Aligned with Architecture V2 theoretically
- Implementation would affect multiple layers or components
- Design is not yet clear enough to estimate complexity
- One or more research questions (from Research Lab) must be answered first
- May require changes to the architecture document or invariants

### Exit Criteria

- Research questions are resolved or sufficiently bounded
- Architecture impact assessment is complete
- Design document exists
- Risk is reduced to YELLOW or GREEN level
- Re-reviewed and either promoted to YELLOW/GREEN or moved to graveyard

### Examples

- Reasoning Engine design (affects Layers 5–7)
- Decision Approval Engine design (affects Layer 8)
- Scarce Resources Model (affects Layer 13)
- Innovation System itself (this file set — must be kept clean and not grow unbounded)

### Required Review Depth

Deep — full answers plus architecture impact assessment. Project lead review with architecture consultation.

---

## RED — Operational Risk

### Definition

Ideas that could destabilize the operational MVP, affect execution of decisions, touch real or simulated capital allocation, or increase autonomy level. RED ideas are not just risky — they are the most architecturally significant decisions the project can make.

### Entry Criteria

- Touches execution path, risk guards, or capital allocation
- Changes autonomy level (Level 0 → 1, Level 1 → 2)
- Modifies how decisions are made or executed
- Changes the operational database schema
- Could cause the system to lose money (even in paper trading)

### Exit Criteria

- Decision Approval Engine exists and is validated
- Evidence from 100+ approved decisions exists
- Auto-Approval Readiness Score exceeds threshold for the specific decision class
- All RED-level review questions answered with evidence
- Contingency plan exists and is tested
- Re-reviewed and either promoted to ORANGE (with reduced risk) or remains RED

### Examples

- Live execution (real capital)
- Level 2 autonomy (auto-execute with approval)
- Changes to PaperTradingEngine
- Changes to risk guards
- Changes to Council voting logic
- Changes to agent decision logic

### Required Review Depth

Maximum — full answers, architecture impact, operational risk assessment, contingency plan, evidence review. Project lead + external review if available.

**RED lane has a hard rule:** No idea may exit RED until evidence proves it is safe. The burden of proof is on the idea, not on the system.

---

## Lane Transition Rules

```
PROPOSED IDEA
    │
    ├──→ GREEN (if safe, additive, independent)
    ├──→ YELLOW (if valuable but premature)
    ├──→ ORANGE (if research needed or architectural impact)
    ├──→ RED (if touches execution or autonomy)
    └──→ GRAVEYARD (if rejected)
    
Promotion (less risk):
    ORANGE → YELLOW (when research questions are resolved)
    YELLOW → GREEN (when dependencies are met)
    RED → ORANGE (when risk is reduced and design is clear)
    
Demotion (more risk or lower priority):
    GREEN → YELLOW (if discovered complexity is higher than expected)
    GREEN/YELLOW → GRAVEYARD (if evidence shows idea is not working)
    
Ideas can move in either direction. Promotion is not permanent — 
evidence may later require demotion.
```

---

## Lane Summary

| Aspect | GREEN | YELLOW | ORANGE | RED |
|--------|-------|--------|--------|-----|
| Risk | Very low to low | Low to medium | Medium to high | High to very high |
| Affects execution? | No | No | Possibly | Yes |
| Affects architecture? | No | No | Yes | Yes |
| Requires research? | No | No | Yes | Yes |
| Can implement now? | Yes | No | No | No |
| Review depth | Light | Standard | Deep | Maximum |
| Scarce resources risk | None | Low | Medium | High |

---
