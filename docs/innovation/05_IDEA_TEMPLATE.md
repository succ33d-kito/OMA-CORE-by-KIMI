# Idea Card Template

*Version 1.0 — June 2026*

---

## Instructions

Use this template for every new idea entering the Innovation Engine. Fill every field. If a field cannot be filled, that is itself a signal — it means the idea is not yet fully formed and may need more research before review.

Mark unknown fields with `[UNKNOWN]`. Fields that genuinely do not apply can be marked `[N/A]`.

---

## Template

```
┌─────────────────────────────────────────────────────────────────────┐
│                          IDEA CARD                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Idea Name:       [Concise, descriptive name]                        │
│  Date:            [YYYY-MM-DD]                                       │
│  Proposed By:     [Name]                                             │
│  Lane:            [GREEN / YELLOW / ORANGE / RED]                    │
│  Current Verdict: [IMPLEMENT NOW / STRATEGIC BACKLOG /               │
│                    RESEARCH LAB / IDEA GRAVEYARD]                     │
│  Risk Color:      [GREEN / YELLOW / ORANGE / RED]                    │
│  Status:          [PROPOSED / REVIEWED / CLASSIFIED / DESIGNED /     │
│                    EXPERIMENT_READY / IMPLEMENTED /                   │
│                    VALIDATED / FAILED / ARCHIVED]                     │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Problem Solved:                                                     │
│  ------------------------------------------------------------------- │
│  [What specific problem does this idea solve? Be precise.             │
│   "The system cannot currently..." is a good start.]                  │
│                                                                      │
│  User Pain:                                                          │
│  ------------------------------------------------------------------- │
│  [Who experiences this problem and how does it affect them?]         │
│                                                                      │
│  Core Hypothesis:                                                    │
│  ------------------------------------------------------------------- │
│  [We believe that implementing [this idea] will produce [this        │
│   outcome] because [this reasoning]. Must be testable.]              │
│                                                                      │
│  First-Principles Reasoning:                                         │
│  ------------------------------------------------------------------- │
│  [Which first-principles document(s) support or challenge this       │
│   idea? What principles does it serve?]                              │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  How It Improves Criterion:                                          │
│  ------------------------------------------------------------------- │
│  [Does this idea help the system judge what matters? How?]           │
│                                                                      │
│  How It Improves Decision Quality:                                   │
│  ------------------------------------------------------------------- │
│  [Does this idea help the system make better choices? How?]          │
│                                                                      │
│  Scarce Resources Improved:                                          │
│  ------------------------------------------------------------------- │
│  [Which of the eight scarce resources does this protect or increase? │
│   Capital / Time / Attention / Knowledge / Relationships /           │
│   Mobility / Health / Freedom of Decision]                           │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Expected Impact:                                                    │
│  ------------------------------------------------------------------- │
│  [What measurable change will this idea produce?]                    │
│                                                                      │
│  Complexity:        [LOW / MEDIUM / HIGH / VERY HIGH]                │
│  Risk:              [VERY LOW / LOW / MEDIUM / HIGH / VERY HIGH]     │
│  One-Person Maintainability: [YES / CONDITIONAL / NO]               │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Dependencies:                                                       │
│  ------------------------------------------------------------------- │
│  [What must exist before this idea can be implemented?]              │
│                                                                      │
│  Validation Method:                                                  │
│  ------------------------------------------------------------------- │
│  [How will we test whether this idea works?]                         │
│                                                                      │
│  Success Criteria:                                                   │
│  ------------------------------------------------------------------- │
│  [What must be true for this idea to be considered successful?       │
│   Must be measurable.]                                               │
│                                                                      │
│  Failure Criteria:                                                   │
│  ------------------------------------------------------------------- │
│  [What would prove this idea is not working or not worth pursuing?   │
│   Must be measurable. If you cannot define failure, the idea is      │
│   not yet testable.]                                                 │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Implementation Boundary:                                            │
│  ------------------------------------------------------------------- │
│  [What is included? What is explicitly excluded? Being precise       │
│   about what this idea does NOT do prevents scope creep.]            │
│                                                                      │
│  What It Must NOT Touch:                                             │
│  ------------------------------------------------------------------- │
│  [Operational execution? Collectors? Council? Agents? Databases?    │
│   Test stability? List specific boundaries.]                         │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Evidence Required:                                                  │
│  ------------------------------------------------------------------- │
│  [What specific evidence would support or contradict this idea?]     │
│                                                                      │
│  Promotion Condition:                                                │
│  ------------------------------------------------------------------- │
│  [What must happen for this idea to move to a higher priority lane?] │
│                                                                      │
│  Kill Condition:                                                     │
│  ------------------------------------------------------------------- │
│  [What would cause this idea to be moved to the graveyard or         │
│   deprioritized?]                                                    │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Review Questions:                                                   │
│  ------------------------------------------------------------------- │
│  [Specific questions the reviewer should consider]                    │
│                                                                      │
│  Final Recommendation:                                               │
│  ------------------------------------------------------------------- │
│  [IMPLEMENT NOW / STRATEGIC BACKLOG / RESEARCH LAB /                 │
│   IDEA GRAVEYARD]                                                    │
│                                                                      │
│  Next Review Date:  [YYYY-MM-DD]                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Filling Guide

| Field | Guidance |
|-------|----------|
| **Idea Name** | Use a noun phrase that clearly identifies the concept. Avoid marketing names. |
| **Lane** | From lane definitions (07_INNOVATION_LANES.md). GREEN if safe, YELLOW if premature, ORANGE if architectural risk, RED if operational risk. |
| **Current Verdict** | Initial classification. May change during review. |
| **Risk Color** | GREEN = no risk to operational system. YELLOW = minor risk. ORANGE = architectural impact. RED = could destabilize or cause losses. |
| **Problem Solved** | Be concrete. If you cannot state the problem in one paragraph, the idea is not yet clear. |
| **Core Hypothesis** | Must be falsifiable. "We believe X will produce Y because Z." |
| **One-Person Maintainability** | YES = one person can build and maintain it. CONDITIONAL = one person can build it but maintenance requires discipline. NO = requires a team. |
| **Validation Method** | If you cannot describe how to test it, you cannot know if it works. |
| **Failure Criteria** | This is the most important field. If you cannot define failure, you cannot kill the idea when it is not working. |
| **Implementation Boundary** | Prevents scope creep. "This idea does X. It does NOT do Y." |
| **What It Must NOT Touch** | Protection against accidental destabilization. Be specific about existing systems. |
| **Promotion/Kill Conditions** | Define in advance so decisions are evidence-based, not emotional. |

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|-------------|--------------|
| Leaving fields blank | A blank field hides uncertainty. If you do not know, say [UNKNOWN]. |
| Vague success criteria | "Works well" is not measurable. "Reduces notification frequency by 50% without increasing missed opportunities" is measurable. |
| No failure criteria | If you cannot define failure, you can never conclude the idea is not working. It becomes immortal. |
| Overbroad boundaries | "Doesn't touch anything important" is not specific. Name the modules and systems it must not touch. |
| Assuming implementation is the goal | The goal is validated learning, not implemented features. |

---
