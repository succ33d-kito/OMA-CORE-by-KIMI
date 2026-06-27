# Idea Lifecycle

*Version 1.0 — June 2026*

---

## Purpose

Every idea in the Innovation Engine follows a defined lifecycle from proposal through validation or rejection. The lifecycle ensures that ideas do not stagnate, that decisions are recorded, and that the project can track its own evolution.

---

## Lifecycle States

```
PROPOSED
    │
    ▼
REVIEWED
    │
    ▼
CLASSIFIED
    │
    ├──→ GRAVEYARD (rejected during classification)
    │
    ▼
DESIGNED
    │
    ├──→ STRATEGIC BACKLOG (designed but deferred)
    │
    ▼
EXPERIMENT_READY
    │
    ├──→ WAITING (dependencies not yet met)
    │
    ▼
IMPLEMENTED
    │
    ├──→ VALIDATED (evidence confirms hypothesis)
    ├──→ FAILED (evidence contradicts hypothesis)
    └──→ ARCHIVED (no longer relevant, superseded, or abandoned)
```

### State Definitions

| State | Definition | Evidence Required | Max Duration |
|-------|------------|-------------------|--------------|
| **PROPOSED** | Idea has been submitted. Not yet reviewed. | None — idea card with basic fields filled | 2 weeks |
| **REVIEWED** | Idea has passed the 14-question review protocol. Verdict assigned. | Completed review with verdict | 1 month if IMPLEMENT NOW; 3 months otherwise |
| **CLASSIFIED** | Idea has been assigned to a lane and has a risk assessment. | Lane assignment, risk color, implementation boundary | 1 month |
| **DESIGNED** | Idea has a design document. Architecture impact assessed. | Design document (may be brief for GREEN, detailed for ORANGE/RED) | 3 months |
| **EXPERIMENT_READY** | Design is complete. Implementation can begin when dependencies are met. | Approved design, dependency check | N/A (waiting state) |
| **IMPLEMENTED** | Idea has been built and deployed on USB. | Working code (for GREEN), passing tests | N/A |
| **VALIDATED** | Implementation has produced evidence that it works. | Evidence meeting success criteria defined in idea card | N/A |
| **FAILED** | Implementation produced evidence that it does not work. | Evidence meeting failure criteria defined in idea card | N/A |
| **ARCHIVED** | Idea is no longer active. Moved to graveyard or superseded. | Documented rationale | Permanent |

---

## Transition Rules

### Allowed Transitions

| From | To | Condition |
|------|----|-----------|
| PROPOSED | REVIEWED | Idea card submitted with all required fields |
| PROPOSED | GRAVEYARD | Rejected during initial review (trivially misaligned) |
| REVIEWED | CLASSIFIED | Lane assigned, risk assessed |
| REVIEWED | GRAVEYARD | Rejected during review (misaligned, too complex, untestable) |
| CLASSIFIED | DESIGNED | Design document produced |
| CLASSIFIED | GRAVEYARD | Rejected during classification (risk too high, dependencies impossible) |
| DESIGNED | EXPERIMENT_READY | Design approved, dependencies identified |
| DESIGNED | STRATEGIC_BACKLOG | Design valid but implementation is premature |
| DESIGNED | GRAVEYARD | Design reveals fatal flaw |
| EXPERIMENT_READY | IMPLEMENTED | Dependencies met, implementation begins |
| IMPLEMENTED | VALIDATED | Success criteria met |
| IMPLEMENTED | FAILED | Failure criteria met |
| IMPLEMENTED | ARCHIVED | No longer relevant, superseded, or abandoned |
| VALIDATED | ARCHIVED | Successfully validated, enters maintenance |
| FAILED | ARCHIVED | Documented failure, moves to graveyard |

### Non-Allowed Transitions (Anti-Patterns)

| Transition | Why Prohibited |
|------------|----------------|
| PROPOSED → IMPLEMENTED | Bypasses review. No idea may be implemented without review. |
| REVIEWED → IMPLEMENTED | Bypasses classification and design. Even simple ideas need lane assignment. |
| CLASSIFIED → IMPLEMENTED | Bypasses design. Every idea must have a design, even if brief. |
| FAILED → IMPLEMENTED | Repeating a failed idea without new evidence. Must return to PROPOSED or REVIEWED. |
| ARCHIVED → IMPLEMENTED | Resurrecting an archived idea without re-review. Must return to PROPOSED. |
| GRAVEYARD → IMPLEMENTED | Resurrecting a rejected idea without re-review. Must return to PROPOSED. |

---

## Backward Movement

Ideas can move backward in the lifecycle when new evidence or changed conditions warrant it.

| Movement | Trigger | Action |
|----------|---------|--------|
| IMPLEMENTED → DESIGNED | Implementation reveals design flaw | Redesign and re-implement |
| IMPLEMENTED → RESEARCH LAB | Implementation reveals unanswered question | Move to research, resolve question |
| EXPERIMENT_READY → DESIGNED | Dependency changes or new constraints | Update design |
| DESIGNED → CLASSIFIED | Lane changes (risk increased) | Reclassify |
| CLASSIFIED → REVIEWED | Fundamental assumptions challenged | Re-review |
| STRATEGIC_BACKLOG → DESIGNED | Evidence supports promotion | Reactivate design |
| STRATEGIC_BACKLOG → GRAVEYARD | Evidence shows idea should not be implemented | Archive |

---

## Evidence Requirements by State Transition

| Transition | Evidence Required |
|------------|-------------------|
| PROPOSED → REVIEWED | Completed idea card with all fields. The 14 review questions answered. |
| REVIEWED → CLASSIFIED | Lane assignment rationale. Risk assessment. Implementation boundary defined. |
| CLASSIFIED → DESIGNED | Design document covering: approach, components, interfaces, data model, test plan, integration points. |
| DESIGNED → EXPERIMENT_READY | Design review complete. Dependencies identified and tracked. Success and failure criteria final. |
| EXPERIMENT_READY → IMPLEMENTED | All dependencies met. Test plan ready. Implementation branch created. |
| IMPLEMENTED → VALIDATED | Evidence meeting success criteria. Test results. User feedback (if applicable). |
| IMPLEMENTED → FAILED | Evidence meeting failure criteria. Analysis of why it failed. Lessons documented. |

---

## Anti-Patterns

| Anti-Pattern | Description | Prevention |
|-------------|-------------|------------|
| **Zombie ideas** | Ideas that stay in REVIEWED or CLASSIFIED forever without progressing. | Set max duration for each state. Ideas that exceed the limit must be either promoted or moved to graveyard. |
| **Pet ideas** | Ideas that are protected from review because someone is attached to them. | The review protocol applies equally to all ideas regardless of who proposed them. |
| **Scope creep** | An idea that expands beyond its original boundary during implementation. | The implementation boundary is defined at classification and cannot be changed without re-review. |
| **Premature promotion** | Moving an idea to IMPLEMENTED before design is complete. | The transition rules prohibit skipping states. Every state must be passed. |
| **Graveyard resurrection** | Pulling an idea from the graveyard without addressing the original rejection reason. | Graveyard ideas must return to PROPOSED and go through full review. The original rejection reason must be explicitly addressed in the new proposal. |
| **Implementation without validation** | Building something and declaring it done without testing whether it works. | Every IMPLEMENTED idea must have a path to VALIDATED or FAILED defined in advance. |

---

## Lifecycle Timing

| Phase | Typical Duration | When to Escalate |
|-------|-----------------|------------------|
| PROPOSED → REVIEWED | 1–7 days | If not reviewed within 2 weeks |
| REVIEWED → CLASSIFIED | 1–3 days | If not classified within 1 week |
| CLASSIFIED → DESIGNED | 1–4 weeks (varies by lane) | If design takes longer than estimated |
| DESIGNED → EXPERIMENT_READY | 1–2 weeks | If dependencies are not tracking |
| EXPERIMENT_READY → IMPLEMENTED | Varies by scope | If blocked for more than 1 review cycle |
| IMPLEMENTED → VALIDATED/FAILED | 1–3 months | If no validation evidence after 3 months |

---
