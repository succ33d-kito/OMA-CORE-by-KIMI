# Design Principles

*Principles that guide all future architecture and implementation decisions.*

---

### Principle 1 — Architecture Follows Philosophy

Every architectural decision should trace back to a philosophical principle. If a component cannot be justified by the project's theory, laws, or north star, it should not exist.

**Application:** Before adding any component, ask: what principle from the Theory or Laws does this serve? If none, reconsider.

---

### Principle 2 — Evidence Before Intuition

Intuition is useful for generating hypotheses. It is not useful for validating them. Every claim about system behavior, performance, or improvement must be supported by evidence.

**Application:** New features should include a validation plan. Features without validation plans are speculative.

---

### Principle 3 — Simple Before Complex

The simplest explanation that accounts for the evidence is preferred. Complexity should be added only when evidence demonstrates that the simpler approach is insufficient.

**Application:** When two designs would both work, prefer the one with fewer components, fewer dependencies, and fewer assumptions.

---

### Principle 4 — Everything Measurable

If a concept cannot be measured, it cannot be improved. Every important concept in the system — confidence, evidence quality, hypothesis accuracy, criterion development — should have an operational definition that can be measured.

**Application:** Before adding a concept to the system, define how it will be measured. Concepts without measurement plans are candidates for future addition, not immediate implementation.

---

### Principle 5 — Every Feature Justifies Itself

No feature exists by default. Each must demonstrate that its benefits exceed its costs — including the cost of complexity, maintenance, cognitive load, and opportunity cost of not building something else.

**Application:** Feature proposals should include a cost-benefit analysis. The burden of proof is on the proposer.

---

### Principle 6 — Criterion Over Prediction

When prediction and criterion conflict, criterion wins. A system that predicts accurately but learns nothing is less valuable than a system that predicts poorly but learns from every outcome.

**Application:** Learning mechanisms should be prioritized over prediction mechanisms. A prediction model that cannot explain its errors is a liability.

---

### Principle 7 — Consequences Over Events

Events are the lowest unit of analysis. Consequences are the unit of meaning. The system should organize its perception around consequences, not events.

**Application:** Event storage is necessary but not sufficient. The system should also store the consequence hypotheses that events generate, and update them as new evidence arrives.

---

### Principle 8 — Learning Over Memorization

Memorization stores outcomes. Learning extracts patterns from outcomes. The system should prioritize the ability to extract generalizable patterns over the ability to recall specific outcomes.

**Application:** Evaluation should measure not just whether the system repeats correct decisions, but whether it avoids repeating incorrect ones.

---

### Principle 9 — Long-Term Over Short-Term

A decision that produces short-term gain at the expense of long-term criterion is a bad decision. The system should be designed to optimize over years, not days.

**Application:** Time horizons should be explicit in every hypothesis. The system should track whether its short-term decisions align with its long-term trajectory.

---

### Principle 10 — Build for Ten Years

Any architecture that cannot survive a decade of evolution is not worth building today. Choose technologies, patterns, and abstractions that can be maintained, replaced, or evolved over long time scales.

**Application:** Avoid tight coupling to specific frameworks, APIs, or models. Dependencies should be replaceable. The philosophy should outlive any specific implementation.

---

### Principle 11 — Validate Continuously

Validation is not a phase. It is a continuous process. Every component, every assumption, every hypothesis should be under continuous validation.

**Application:** The system should include mechanisms for self-evaluation — not just of outcomes, but of the quality of its own reasoning.

---

*These principles are not rules to be enforced by process. They are heuristics to guide judgment. When principles conflict, the conflict itself is information — it reveals where the system's theory is incomplete.*
