# Innovation Engine

## The Scientific Laboratory for Ideas

*Version 1.0 — June 2026*
*Canonical Reference: docs/ARCHITECTURE_V2.md*

---

## 1. What the Innovation Engine Is

The Innovation Engine is **the project's internal scientific laboratory for ideas**.

It is not a TODO list. It is not a Kanban board. It is not a feature wishlist. It is a disciplined system for managing the evolution of O.M.A.-C.O.R.E. itself — applying the same rigor to project ideas that the system applies to market hypotheses.

Every idea entering the Innovation Engine is treated as a hypothesis until validated. Enthusiasm is not evidence. Complexity must justify itself. Every idea must protect or increase scarce resources.

---

## 2. Core Thesis

O.M.A.-C.O.R.E. must manage its own evolution with the same discipline it expects from its decision system.

If the system demands:
- Evidence before action
- Falsifiable hypotheses
- Measurable outcomes
- Learning from failure
- Protection of scarce resources

Then the project itself must follow the same rules.

The Innovation Engine is the mechanism that ensures this.

---

## 3. The Innovation Loop

```
Idea (any source: observation, frustration, ambition, research)
    ↓
Review (challenge assumptions, check alignment)
    ↓
Hypothesis ("We believe this idea will improve Criterion because...")
    ↓
Evidence Needed (what would prove or disprove it)
    ↓
Experiment (the smallest safe test)
    ↓
Outcome (what actually happened)
    ↓
Validated Learning (what we now know)
    ↓
Criterion Update (the project's judgment improved)
    ↓
Adopt / Revise / Archive / Reject
         ↓
         └──→ (loop back to Idea or exit to Graveyard)
```

This loop mirrors the Scientific Learning Flow from ARCHITECTURE_V2.md. Ideas follow the same lifecycle as hypotheses because they are hypotheses — beliefs about what will improve the project.

---

## 4. Design Principles for the Innovation Engine

| Principle | Meaning |
|-----------|---------|
| **Ideas are hypotheses** | Every idea is a belief about what will improve Criterion. It must be testable and falsifiable. |
| **Enthusiasm is not evidence** | Excitement about an idea does not make it correct. Evidence must be produced. |
| **Complexity must justify itself** | Every component added increases maintenance burden. The benefit must clearly exceed the cost. |
| **Protect scarce resources** | Every idea must protect or increase at least one scarce resource (capital, time, attention, knowledge, relationships, mobility, health, freedom of decision). Ideas that consume resources without producing them are net negative. |
| **One-person maintainability** | The project is built and maintained by one person. An idea that requires a team to implement or maintain must be deferred, simplified, or rejected. |
| **Operational stability first** | No idea may destabilize the operational MVP. The laptop version must continue running while the USB version innovates. |
| **No idea is sacred** | Any idea can be challenged, demoted, archived, or rejected. The project is not attached to its ideas — it is attached to its evidence. |

---

## 5. What the Innovation Engine Produces

| Output | Description |
|--------|-------------|
| **IMPLEMENT NOW** | Green-lane ideas ready for development on USB |
| **STRATEGIC BACKLOG** | Aligned but premature ideas — valuable but not yet actionable |
| **RESEARCH LAB** | Open questions requiring experiments before design can begin |
| **IDEA GRAVEYARD** | Rejected or archived ideas with documented rationale |
| **Review Cadence** | Daily, weekly, monthly, quarterly review rhythms |
| **Idea Lifecycle** | Tracked status of every active idea from proposal to validation |

---

## 6. Relationship to Architecture V2

The Innovation Engine lives in Layer 14 of the layered architecture (ARCHITECTURE_V2.md §5). It is a support system — it does not execute trades, form hypotheses about markets, or make operational decisions. It manages the project's own evolution.

It consumes:
- Project observation (what is working, what is not)
- Research findings (from `research/` and `docs/first_principles/`)
- Operational evidence (from telemetry, test results, Extended Demo data)

It produces:
- Prioritized implementation guidance
- Documented decisions about what not to build
- Evidence of the project's own learning over time

---

## 7. File Structure

| File | Purpose |
|------|---------|
| `00_INNOVATION_ENGINE.md` | This file — overview, thesis, principles |
| `01_IMPLEMENT_NOW.md` | Green-lane ideas ready for implementation |
| `02_STRATEGIC_BACKLOG.md` | Aligned but premature ideas |
| `03_RESEARCH_LAB.md` | Open research questions |
| `04_IDEA_GRAVEYARD.md` | Rejected or archived ideas |
| `05_IDEA_TEMPLATE.md` | Reusable Idea Card template |
| `06_REVIEW_PROTOCOL.md` | Standing review protocol |
| `07_INNOVATION_LANES.md` | Lane definitions (green/yellow/orange/red) |
| `08_IDEA_LIFECYCLE.md` | Lifecycle states and transitions |
| `09_REVIEW_CADENCE.md` | Review rhythms and decision rules |
| `ideas_registry.json` | Machine-readable idea registry |

---
