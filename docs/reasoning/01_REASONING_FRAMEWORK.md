# Reasoning Framework

*Version 1.0 — June 2026*
*Learning Core — Layer 5*
*Canonical Reference: docs/ARCHITECTURE_V2.md, docs/learning_core/01_REASONING_ENGINE.md*

---

## 1. Purpose

The Reasoning Framework defines how O.M.A.-C.O.R.E. transforms events into hypotheses through multiple independent reasoning modes. It is the cognitive layer of the system — the mechanism that interprets what happened, considers why it matters, and generates testable beliefs about consequences.

This framework does not replace agents. It does not replace the Council. It operates between them, adding a structured reasoning layer that transforms agent interpretations into scientific hypotheses.

---

## 2. Core Thesis

Good hypotheses emerge from diverse reasoning modes, not from a single model output.

A single reasoning approach — whether technical analysis, fundamental analysis, or pattern matching — is blind to the perspectives it does not use. Multiple reasoning modes looking at the same event from different logical perspectives produce richer, more robust hypotheses.

The system does not need the "correct" reasoning mode. It needs enough diverse modes that the truth is likely to be captured by at least one of them, and that competing hypotheses can be tested against each other.

---

## 3. Agents vs Reasoning Modes

| Aspect | Agents | Reasoning Modes |
|--------|--------|-----------------|
| **Role** | Domain interpreters | Cognitive perspectives |
| **Input** | Market data, events | Events + agent opinions + context |
| **Output** | AgentOpinion (recommendation, confidence, reasoning) | Scenario candidates, hypothesis candidates |
| **Scope** | One domain per agent (market, news, macro, risk, trend) | Cross-domain logical modes |
| **Knowledge** | Static rules, no learning | Learnable — mode performance is tracked |
| **Relationship** | Agents produce the raw material | Reasoning modes structure it into hypotheses |
| **Example** | MarketAgent: "RSI < 30, price may bounce" | Causal mode: "RSI < 30 + bullish divergence = mean reversion hypothesis" |

Agents answer: "What does the data say about this domain?"

Reasoning modes answer: "What kind of thinking should we apply to this situation?"

---

## 4. Why Reasoning Does Not Replace Agents

Agents are the system's sensors. They convert raw market data into structured opinions. Each agent has a specific analytical domain — technical, news, macro, risk, trend. Removing agents would remove the system's ability to interpret domain-specific information.

Reasoning modes operate on the output of agents. They take the opinions, evidence, and reasoning that agents produce and apply cognitive frameworks to transform them into hypotheses. Without agents, reasoning modes would have no raw material. Without reasoning modes, agents produce opinions that never become testable beliefs.

Both are required. Neither replaces the other.

---

## 5. Why the Council Should Eventually Evaluate Reasoning Outputs

The Agent Council currently evaluates agent opinions and produces a weighted decision. This is correct for the operational layer — it answers "what should we do?"

The Reasoning Council (future, `03_REASONING_COUNCIL.md`) evaluates reasoning mode outputs. It answers: "which hypotheses are worth testing?"

These are different questions requiring different evaluation criteria:

| Council Type | Evaluates | Produces | Criteria |
|-------------|-----------|----------|----------|
| Agent Council | AgentOpinions | CouncilDecision (action) | Agent track record, conviction |
| Reasoning Council | Scenario candidates | Prioritized hypotheses | Falsifiability, novelty, evidence strength |

The two councils operate in sequence:

```
Event → Agents → AgentOpinions → Agent Council → CouncilDecision → Execution
                                        ↓
                                Reasoning Modes → Scenario Candidates → Reasoning Council → Prioritized Hypotheses → Scientific Store
```

The Agent Council makes the operational decision (act or not). The Reasoning Council makes the scientific decision (which hypotheses to create). They are independent.

---

## 6. High-Level Flow

```
Raw Event (from EventBus)
    │
    ▼
Step 1: Agent Interpretation
    ├── MarketAgent interprets price action
    ├── NewsAgent interprets news context
    ├── MacroAgent interprets macro conditions
    ├── RiskAgent assesses risk context
    └── TrendAgent identifies trend regime
    │
    ▼
Step 2: Reasoning Modes (12 modes)
    ├── Each mode receives the event + agent opinions
    ├── Each mode applies its cognitive perspective
    └── Each mode produces scenario candidates
    │
    ▼
Step 3: Scenario Candidates
    ├── All scenario candidates collected
    ├── Duplicates merged
    └── Candidates tagged with source reasoning mode(s)
    │
    ▼
Step 4: Reasoning Council
    ├── Evaluate each scenario candidate
    ├── Score: falsifiability, novelty, evidence strength, resource feasibility
    └── Produce prioritized, filtered list
    │
    ▼
Step 5: Hypothesis Formulation
    ├── Each surviving scenario becomes a hypothesis
    ├── Falsifiability gate: all required fields populated
    └── Hypothesis created in Scientific Store
    │
    ▼
Step 6: Feedback
    ├── Mode performance tracked over time
    ├── Modes that produce confirmed hypotheses gain weight
    └── Modes that produce rejected hypotheses lose weight
```

---

## 7. Role of the Reasoning Framework

| Function | Description |
|----------|-------------|
| **Define reasoning modes** | Specify the 12+ cognitive perspectives the system can apply |
| **Define mode evaluation** | Track which modes produce good hypotheses over time |
| **Define mode combination** | How multiple mode outputs are combined into coherent hypothesis candidates |
| **Define the Reasoning Council** | How divergent mode outputs are resolved, preserved as competing hypotheses, or discarded |
| **Define the hypothesis gate** | The strict requirements a scenario must meet to become a hypothesis |
| **Define feedback loops** | How reasoning performance feeds back into mode weighting and Criterion |

---

## 8. Boundaries

| Boundary | Rule |
|----------|------|
| **No write to operational pipeline** | Reasoning modes read from agents and events but never write to them |
| **No decision override** | Reasoning does not override the Agent Council's operational decisions |
| **No execution** | Reasoning never triggers or modifies execution |
| **No real-time latency requirement** | Reasoning can run asynchronously after the operational decision |
| **No single mode dependency** | The system must function even if a reasoning mode fails or produces no output |

---

## 9. What It Must Never Do

1. **Never replace agents.** Reasoning modes are cognitive frameworks, not domain sensors. Without agent input, reasoning modes have no raw material.
2. **Never delay operational decisions.** The operational pipeline (event → decision → execution) must not wait for reasoning. Reasoning runs in parallel or after.
3. **Never produce unfalsifiable hypotheses.** Every reasoning mode output that reaches the hypothesis gate must meet falsifiability requirements.
4. **Never hide disagreement.** When reasoning modes disagree, competing hypotheses must be preserved — not averaged away.
5. **Never become a monolithic model.** The power of the framework is diversity. Consolidating reasoning modes into a single model would lose the benefit.

---

## 10. How It Supports Criterion

The Reasoning Framework directly feeds Criterion evolution (docs/learning_core/03_CRITERION_EVOLUTION.md):

| Criterion Dimension | How Reasoning Framework Contributes |
|---------------------|-------------------------------------|
| Hypothesis Quality | Better reasoning produces more specific, falsifiable, testable hypotheses |
| Decision Quality | Hypotheses linked to reasoning modes enable post-hoc evaluation of which thinking patterns produced good decisions |
| Error Recurrence | Reasoning mode performance tracking reveals which modes consistently produce errors |
| Knowledge Yield | Reasoning modes that generate confirmed hypotheses contribute more to knowledge |
| Learning Velocity | The system learns which reasoning modes work in which conditions, improving faster |

---

## 11. How It Protects One-Person Maintainability

| Strategy | Implementation |
|----------|---------------|
| **Modular modes** | Each reasoning mode is independent. One person can implement, test, and maintain modes one at a time. |
| **Progressive rollout** | V1 implements only 4 required modes. Additional modes are V2+ optional. |
| **Shared infrastructure** | All modes use the same input/output format, evaluation framework, and persistence. No duplicated infrastructure. |
| **Default outputs** | If a mode produces no output (e.g., insufficient data), the system continues without it. No mode is critical. |
| **Self-evaluating** | Mode performance tracking automatically identifies underperforming modes, reducing manual review burden. |

---
