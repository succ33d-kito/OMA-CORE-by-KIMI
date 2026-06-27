# Idea Graveyard

*Version 1.0 — June 2026*
*Lane: GRAVEYARD — Rejected or archived*

---

## Purpose

The Idea Graveyard preserves rejected ideas and the reasons for their rejection so that the project does not repeatedly revisit the same mistakes. An idea in the graveyard is not necessarily wrong forever — it may have a reconsideration condition. But it is not active, not planned, and not researched.

Reasons for internment:
- **Misalignment** — does not serve Criterion, decision quality, or scarce resources
- **Prematurity** — valuable but too early (better served by Strategic Backlog)
- **Complexity** — exceeds one-person maintainability constraint
- **Evidence gap** — insufficient evidence that the idea would work
- **Anti-goal violation** — conflicts with the project's anti-goals (11_ANTI_GOALS.md)
- **Superseded** — a better approach replaced this idea

---

## Graveyard Entries

---

### G-01: Build Every Interesting Agent Immediately

**Why tempting:** Each new data source suggests a new agent. More agents = more coverage = better decisions, intuitively.

**Why rejected now:**
- Agents are frozen static rules. More agents means more frozen rules, not more learning.
- Each agent adds maintenance burden, test surface, and cognitive load.
- The bottleneck is not agent quantity — it is hypothesis quality. One good hypothesis beats ten agents.
- The object model prioritizes Hypothesis and Evidence before Agent improvement.
- Violates One-Person Army Constraint (too many components to maintain).

**Reconsideration condition:** When agents can learn from outcomes (not static rules), adding more agents becomes valuable. Until then, maintain current 5 agents.

---

### G-02: Turn O.M.A.-C.O.R.E. into a Generic Chatbot

**Why tempting:** Chatbots are popular. Adding natural language conversation would make the system more accessible and appealing.

**Why rejected now:**
- The system is a decision intelligence system, not a conversational agent. Chat is an interaction modality, not a core capability.
- Conversation optimization competes with decision optimization for development resources.
- Anti-goal (11_ANTI_GOALS.md): "The system should explain its reasoning, not converse. Explanations serve learning. Conversation serves engagement."
- A conversational interface before decision quality exists would give the appearance of intelligence without the substance — the opposite of the project's values.

**Reconsideration condition:** When the system has demonstrable Criterion across multiple domains and a CLI is no longer sufficient for interaction. At that point, a narrow Q&A interface (not a general chatbot) could be considered.

---

### G-03: Optimize Dashboard Aesthetics Before Decision Quality

**Why tempting:** Beautiful dashboards produce satisfying visual feedback. They look like progress.

**Why rejected now:**
- Dashboard aesthetics consume development time without improving decision quality, Criterion, or learning.
- The system's value is in judgment, not visualization.
- A beautiful dashboard with poor decisions is a liability — it creates an illusion of capability.
- The terminal cockpit and basic CLI are sufficient interfaces at this stage.

**Reconsideration condition:** When the system demonstrates consistent decision quality improvement over 6+ months. At that point, a better dashboard may help the user benefit from the system's insights.

---

### G-04: Automate Live Execution Before Evidence-Based Approval

**Why tempting:** Live execution is the ultimate test. Running with real capital would produce real outcomes and real learning.

**Why rejected now:**
- Directly violates Invariant 3 (Every autonomous action must be explainable) and Invariant 6 (Operational stability outranks feature growth).
- The Decision Approval Engine does not exist. There is no mechanism to determine whether a decision is safe to execute.
- Real capital deployment without evidence-based approval is gambling, not science.
- The laptop version runs Extended Demo on paper trading, which produces sufficient data for validation.

**Reconsideration condition:** Decision Approval Engine exists, has processed 100+ decisions with known outcomes, and the Auto-Approval Readiness Score exceeds threshold for at least one decision class.

**This rejection is absolute until the condition is met. No exceptions.**

---

### G-05: Add Markets Before Improving Decision Quality

**Why tempting:** More markets = more opportunities = more data = more learning, intuitively.

**Why rejected now:**
- Adding markets multiplies complexity without addressing the core bottleneck (decision quality).
- The current market set (crypto, stocks, forex, commodities, indices, bonds, macro) is sufficient for validation.
- Additional markets increase collector maintenance, data quality issues, and attention fragmentation.
- The system should first demonstrate it can make good decisions in its existing markets.

**Reconsideration condition:** When the system demonstrates sustained decision quality improvement across all current markets for 6+ months, selective market expansion can be evaluated.

---

### G-06: Treat Criterion as a Single Score

**Why tempting:** A single Criterion score would be easy to track, display, and optimize. It would give a simple answer to "is the system improving?"

**Why rejected now:**
- Invariant 1 (Criterion Is Emergent): "Criterion is never a component, engine, or module. It is not built."
- A single score reduces Criterion to a number, which encourages optimizing the number instead of improving judgment (Goodhart's Law).
- The CRITERION_VALIDATION_FRAMEWORK.md explicitly defines Criterion as converging evidence across multiple dimensions, not a single metric.
- Multi-dimensional measurement is harder but more honest.

**Reconsideration condition:** If evidence after 12+ months of multi-dimensional Criterion tracking shows that a single composite score is equally informative and less complex. Burden of proof is on the composite score.

---

### G-07: Treat Profit as the Only Success Metric

**Why tempting:** Profit is simple, measurable, universally understood, and unambiguous. It aligns with the trading domain.

**Why rejected now:**
- Directly contradicts the project's core thesis. The Manifesto states: "If the system trades profitably but does not improve its judgment, it has failed."
- Profit can come from luck. The North Star is better decisions, not more money.
- Profit-only optimization would sacrifice long-term learning for short-term gains.
- The project's value proposition (Criterion development over time) is incompatible with profit-only evaluation.

**Reconsideration condition:** Never. This idea is permanently rejected. The project's mission is incompatible with profit as the sole metric. If the project ever adopts profit-only evaluation, it has ceased to be O.M.A.-C.O.R.E.

**This internment is permanent.**

---

## Graveyard Summary

| # | Idea | Rejection Reason | Permanence |
|---|------|------------------|------------|
| G-01 | Build every interesting agent immediately | Complexity, premature, anti-goal | Conditional |
| G-02 | Turn into generic chatbot | Misalignment, anti-goal violation | Conditional |
| G-03 | Optimize dashboard aesthetics first | Premature, misaligned priority | Conditional |
| G-04 | Automate live execution before approval | Safety, invariant violation | **Absolute** |
| G-05 | Add markets before improving decisions | Premature, complexity | Conditional |
| G-06 | Criterion as single score | Philosophical contradiction, Goodhart's Law | Conditional |
| G-07 | Profit as only success metric | **Core thesis contradiction** | **Permanent** |

---
