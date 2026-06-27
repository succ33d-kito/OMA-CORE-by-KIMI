# Reasoning Engine

*Version 1.0 — June 2026*
*Learning Core Component — ARCHITECTURE V2 Layer 5*

---

## 1. Executive Summary

The Reasoning Engine fills the single largest gap in the current architecture: the missing step between Event and Hypothesis.

Today, events enter the system and are processed by agents that produce opinions, not hypotheses. The Council weighs these opinions and produces decisions — but there is no structured transformation from "something happened" to "what does this mean and what should we test?"

The Reasoning Engine does not replace agents. It wraps, structures, and elevates their outputs into the hypothesis framework. It transforms raw event interpretation into testable, falsifiable beliefs.

---

## 2. Problem Solved

### Current State

```
Raw Event
    ↓
AgentOpinion (text, unstructured)
    ↓
CouncilDecision (weighted vote, no hypothesis)
    ↓
TradeSignal (direction, confidence)
    ↓
Guard evaluation (binary pass/fail)
```

The system currently answers: "Should we act?" without ever answering: "What do we believe?"

### Target State

```
Structured Event
    ↓
Reasoning Engine
    ├── What happened? (event interpretation)
    ├── Why might it matter? (consequence identification)
    ├── What could follow? (scenario generation)
    ├── Which assets/resources affected? (impact mapping)
    └── What should we test? (hypothesis generation)
    ↓
Hypothesis (testable, falsifiable, with conditions)
    ↓
Evidence (linked to hypothesis, evaluated)
    ↓
Decision (based on hypothesis evaluation, not just vote)
```

---

## 3. Inputs

| Input | Source | Format | Description |
|-------|--------|--------|-------------|
| **Event** | EventBus | `EventData` (source, type, title, timestamp, assets, sentiment, urgency, confidence) | The structured notification that something happened |
| **AgentOpinions** | Agent modules | Text reasoning, recommendation, confidence, evidence list | Each agent's interpretation of the event |
| **Historical context** | Memory, Scientific Store | Recent hypotheses, active evidence, past outcomes in similar contexts | What has been learned about similar situations |
| **Market/domain state** | Market data, Risk | Current volatility, regime, position exposure | The context in which reasoning occurs |
| **Scarce resource state** | Future: Resource tracker | Available capital, attention budget, time constraints | What resources are available to pursue hypotheses |

---

## 4. Outputs

| Output | Destination | Format | Description |
|--------|-------------|--------|-------------|
| **Hypothesis candidates** | Scientific Store, filter | List of proposed hypotheses with all required fields | Testable beliefs about consequences |
| **Discarded candidates** | Internal log | Reasons for rejection | Why some hypotheses were not pursued |
| **Reasoning trace** | DecisionRecord (future) | Structured JSON of the reasoning process | Immutable record of what was considered |
| **Confidence/priority** | Hypothesis field | Float | Relative priority among competing hypotheses |

---

## 5. Reasoning Process

The Reasoning Engine follows a structured pipeline:

```
Event arrives
    │
    ▼
Step 1: INTERPRET — What happened?
    │   Parse event into structured components
    │   Map to known event types and patterns
    │   Identify affected assets, domains, resources
    │
    ▼
Step 2: CONSEQUENCE SCAN — Why might it matter?
    │   Generate potential consequences
    │   Classify by time horizon (immediate/short/medium/long)
    │   Estimate consequence strength (weak/medium/strong)
    │
    ▼
Step 3: SCENARIO GENERATION — What could follow?
    │   For each consequence, generate at least one scenario
    │   Attach invalidation conditions
    │   Estimate probability and impact range
    │
    ▼
Step 4: HYPOTHESIS FORMULATION — What should we test?
    │   Transform each testable scenario into a hypothesis
    │   Ensure falsifiability
    │   Assign initial confidence
    │
    ▼
Step 5: FILTER — Which hypotheses survive?
    │   Apply filters (novelty, duplication, feasibility, resource check)
    │   Prioritize surviving hypotheses
    │
    ▼
Hypothesis candidates emitted
```

### Step Details

#### Step 1: Interpret

The engine receives the structured event and:
- Classifies the event type (market, macro, news, geopolitical, data)
- Maps to affected symbols/assets/domains
- Notes urgency and confidence from the event metadata
- Checks for similar recent events in memory

Output: `EventInterpretation` — a structured representation of what happened.

#### Step 2: Consequence Scan

The engine generates potential consequences:
- What could this event mean for each affected asset?
- What are the immediate consequences (minutes to hours)?
- What are the medium consequences (hours to days)?
- What are the long consequences (days to weeks)?
- What are the second-order effects?

At V1, this is rule-based — mapping event types to consequence templates. V2+ may use learned patterns from past outcomes.

Output: `ConsequenceList` — ranked potential consequences with time horizons.

#### Step 3: Scenario Generation

For each plausible consequence, the engine generates a scenario:
- "If [event] then [consequence] within [timeframe] unless [invalidation condition]"
- Attach estimated impact range
- Attach estimated probability
- Note which conditions would invalidate the scenario

Output: `ScenarioCandidates` — structured predictions ready for hypothesis framing.

#### Step 4: Hypothesis Formulation

Each scenario is transformed into a Hypothesis object:
- Title: concise statement of the belief
- Description: what the hypothesis claims
- Predicted consequence: what outcome is expected
- Conditions: when does this hypothesis apply?
- Invalidation conditions: what would prove it wrong?

The Hypothesis schema (`core/schemas/hypothesis_schema.py`) already defines these fields. The engine populates them.

Output: `HypothesisCandidates` — list of fully formed hypotheses ready for filtering.

#### Step 5: Filter

Each candidate is checked against:
- **Novelty**: Is this substantially different from existing active hypotheses?
- **Duplication**: Does this overlap with an existing hypothesis within 80%+ similarity?
- **Falsifiability**: Can it be proven wrong? (Reject unfalsifiable candidates)
- **Resource feasibility**: Do we have the resources (time, attention, capital) to test this?
- **Priority**: Among surviving candidates, which is most urgent/important?

Output: Filtered and prioritized hypothesis candidates ready for creation.

---

## 6. Hypothesis Candidate Generation

At V1, hypothesis generation works through existing agent output:

```
AgentOpinion { recommendation, confidence, reasoning, evidence }
    │
    ▼
Reasoning Engine wraps each opinion:
    │
    ├── Agent recommends BUY BTC with 0.7 confidence
    │   → Hypothesis: "BTC will increase 2-5% within 24 hours 
    │     due to positive macro sentiment"
    │   → Conditions: macro sentiment remains positive
    │   → Invalidation: BTC drops below entry within 6 hours
    │
    ├── Agent recommends SELL ETH with 0.6 confidence
    │   → Hypothesis: "ETH will decrease 3-6% within 48 hours 
    │     due to resistance at 200-day MA"
    │   → Conditions: volume confirms rejection
    │   → Invalidation: ETH breaks above resistance with volume
    │
    └── Agent recommends HOLD with 0.8 confidence
        → Hypothesis: "No actionable opportunity exists because 
          current conditions do not meet entry criteria"
        → Conditions: no change in current conditions
        → Invalidation: conditions change favorably
```

This ensures that even at V1, the output of agents becomes scientific input.

---

## 7. Hypothesis Filter

| Filter | Description | Threshold | Priority |
|--------|-------------|-----------|----------|
| **Novelty** | Is this hypothesis substantially new? | <80% similarity to any ACTIVE hypothesis | Required |
| **Falsifiability** | Can it be proven wrong? | Must have invalidation_conditions | Required |
| **Time horizon** | Is the prediction timeframe reasonable? | Must specify timeframe | Required |
| **Specificity** | Is the predicted consequence specific enough? | Must be measurable | Required |
| **Confidence floor** | Is confidence above minimum? | >0.2 (configurable) | Required |
| **Resource check** | Can we pursue this hypothesis? | Resources available or allocatable | Advisory |
| **Urgency** | Is the hypothesis time-sensitive? | Based on event urgency | Advisory |

Hypotheses that fail required filters are discarded. Those that fail advisory filters are flagged but may still be created.

---

## 8. Falsifiability Requirements

Every hypothesis generated by the Reasoning Engine MUST have:

1. **A specific predicted consequence.** "BTC will increase" is not specific. "BTC will increase 2-5% within 24 hours of the FOMC minutes release" is specific.
2. **Measurement criteria.** How will we know if the prediction was correct? Must be objective and measurable.
3. **Invalidation conditions.** What observable event would prove this hypothesis wrong before the time horizon expires?
4. **Time horizon.** When will we evaluate this hypothesis? Must be explicit.

The Reasoning Engine rejects any hypothesis candidate that lacks any of these four requirements. This is a hard constraint — it cannot be bypassed.

---

## 9. Novelty Detection

Novelty detection compares a hypothesis candidate against all active hypotheses in the Scientific Store:

- **Title similarity** — cosine similarity or edit distance on the title text
- **Consequence overlap** — do they predict the same outcome for the same asset?
- **Domain overlap** — do they apply to the same domain (crypto, macro, etc.)?
- **Evidence overlap** — do they cite the same evidence sources?

A candidate with >80% similarity across all dimensions is flagged as a duplicate and either merged with the existing hypothesis or discarded with a reason logged.

---

## 10. Duplicate Hypothesis Prevention

| Case | Action |
|------|--------|
| Exact duplicate (same asset, same direction, same predicted consequence) | Discard. Log: "Duplicate of hypothesis [ID]." |
| Near duplicate (same asset, same direction, different predicted consequence magnitude) | Flag. Optionally merge with existing if the new evidence strengthens the existing hypothesis. |
| Overlapping (same asset, different direction) | Keep both. Competing hypotheses are valuable. |
| Same consequence, different asset | Keep both. Cross-asset patterns are worth tracking. |

---

## 11. Relationship to Agents and Council

### Agents

The Reasoning Engine does not replace agents. It transforms their output:

```
AgentOpinion (existing) → Reasoning Engine → Hypothesis (new)
```

Agents continue to produce opinions using their existing logic. The Reasoning Engine runs after the Council decision, wrapping the entire decision context into one or more hypotheses. If multiple agents disagree, the Reasoning Engine generates competing hypotheses rather than trying to resolve the disagreement.

This is critical: disagreement between agents is not a problem to be resolved — it is a source of competing hypotheses to be tested.

### Council

The Council continues to produce decisions. The Reasoning Engine runs alongside the Council, not instead of it:

1. Agents produce opinions → Council produces decision
2. Reasoning Engine reads: event + agent opinions + Council decision + guard results
3. Reasoning Engine produces: hypotheses that explain the decision context
4. Hypotheses are stored in the Scientific Store
5. When the outcome becomes available, the hypothesis is evaluated

Over time, the Council's decision-making can incorporate hypothesis quality. But at V1, the Reasoning Engine is read-only with respect to the Council — it observes and structures, but does not modify.

---

## 12. Relationship to Scientific Layer

The Reasoning Engine is the bridge between operational Layer 4 (Event) and scientific Layer 6 (Hypothesis).

```
Layer 4: Event  ────  Reasoning Engine  ────  Layer 6: Hypothesis
                       (Layer 5)
```

It consumes:
- Events (from EventBus)
- Agent opinions (from Agent modules)
- Council decisions (from Council)
- Guard evaluations (from Execution layer)

It produces:
- Hypotheses (stored in Scientific Store via `scientific_store.create_hypothesis()`)
- Reasoning traces (stored for future DecisionRecord assembly)

It does NOT consume or produce:
- Evidence (Evidence belongs to the lifecycle of a hypothesis, not to its creation)
- Outcomes (Outcomes belong to the execution/observation layer)
- Knowledge (Knowledge is extracted from evaluated hypotheses)

---

## 13. Failure Modes

| # | Failure Mode | Description | Likelihood | Mitigation |
|---|-------------|-------------|------------|------------|
| 1 | **Hypothesis overload** | Every event generates too many hypotheses, flooding the store. | Medium | Strict filtering. Minimum confidence threshold. Maximum hypotheses per event (configurable). |
| 2 | **False novelty** | Similar hypotheses are not recognized as duplicates due to text variation. | Medium | Use structured fields (symbol, direction, timeframe) for comparison, not just text. |
| 3 | **Agent bypass** | Hypotheses are generated that contradict agent opinions without evidence. | Low | At V1, hypotheses should primarily wrap agent outputs. Independent hypothesis generation comes later. |
| 4 | **Reasoning trace explosion** | Storing full reasoning traces for every hypothesis creates storage pressure. | Low | Summarize traces. Archive detailed traces after 30 days. |
| 5 | **Falsifiability bypass** | An unfalsifiable hypothesis slips through the filter. | Low | Hard filter on invalidation_conditions. Do not allow empty or vague conditions. |

---

## 14. Validation Method

| Method | Description | Phase |
|--------|-------------|-------|
| **Unit tests on hypothesis generation** | Verify that given an event and agent opinions, the engine produces valid hypotheses. | Implementation |
| **Falsifiability filter tests** | Verify that unfalsifiable candidates are rejected. | Implementation |
| **Duplicate detection tests** | Verify that similar hypotheses are merged or discarded. | Implementation |
| **Historical replay** | Run the Reasoning Engine on past events and evaluate whether the generated hypotheses would have been useful. | Implementation |
| **Human review** | Manually review a sample of generated hypotheses for quality, novelty, and relevance. | First 30 days |

---

## 15. Implementation Stages

| Stage | Scope | Effort | Dependencies |
|-------|-------|--------|--------------|
| **V1 — Agent output wrapper** | Convert agent opinions into hypotheses using the existing schema. Rule-based. No independent reasoning. | 2-3 days | Scientific Store (exists) |
| **V2 — Structured reasoning** | Add consequence scan, scenario generation, and hypothesis filtering. Still primarily template-based. | 3-5 days | V1 |
| **V3 — Learning from outcomes** | Use past hypothesis evaluations to improve hypothesis generation. Which hypothesis attributes correlate with validation? | 5-7 days | V2, Outcome Bridge, 100+ evaluated hypotheses |
| **V4 — Proactive hypothesis generation** | Generate hypotheses from patterns in data, not just from events. | 7-10 days | V3, Missed Opportunity System, Knowledge Store |

---
