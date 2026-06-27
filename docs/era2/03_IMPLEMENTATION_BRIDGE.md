# Implementation Bridge

## The Engineering Transition from MVP Prototype to Criterion Laboratory

*Version 1.0 — June 2026*

---

## 0. Preamble

ERA I produced the scientific philosophy. ERA II produced the Scientific Object Model — seven objects that define what truly exists in the project's universe.

This document is the bridge between those objects and the code that implements them.

It does not specify frameworks, databases, APIs, or infrastructure. It specifies the minimum sequence of changes required to transform today's MVP — a working signal engine — into a Criterion Laboratory that produces reproducible scientific evidence of learning.

The bridge has three sections:
1. **Where we are** — an honest audit of every component
2. **Where we must go** — the scientific objects we must implement
3. **How to get there** — the prioritized sequence of engineering changes

---

## PART I: Current MVP Audit

### 1.1 Component Inventory

Every significant component of the current MVP was audited. Each is assessed for purpose, maturity, strengths, weaknesses, dependencies, and scientific relevance (how it contributes to the seven scientific objects).

#### Collectors (Data Ingestion)

| Component | Purpose |
|-----------|---------|
| WorldMonitorV2 | Orchestrates all collectors, publishes raw events to EventBus |
| CoinGeckoCollector | Crypto price/volume data |
| YahooFinanceCollector | Stocks, forex, commodities, indices |
| BinanceCollector | Real-time crypto market data |
| FREDCollector | Macroeconomic indicators |
| RSSCollector | News feeds (Reuters, Bloomberg, CoinDesk) |
| SentimentCollector | Crypto Fear & Greed Index |
| PolymarketCollector | Prediction market probabilities |

**Maturity:** Production-ready. Eight collectors running continuously with error handling, retry logic, rate limiting, and stats tracking.

**Strengths:**
- Reliable data ingestion from diverse sources
- Clean BaseCollector abstraction
- WorldMonitorV2 handles scheduling, publishing, error aggregation
- Collectors are independently testable

**Weaknesses:**
- No evidence formation — raw events are published without hypothesis framing
- No source reliability tracking (all sources treated equally)
- No evidence decay or expiration mechanism
- Events are stored but never linked to hypotheses

**Scientific relevance:** Collectors produce raw observations. In the object model, these become Evidence only when linked to a Hypothesis. Currently, they produce Events that are consumed directly by agents without any hypothesis layer.

---

#### Schemas

| Component | Purpose |
|-----------|---------|
| Event | Source, type, title, timestamp, assets, sentiment, urgency, confidence |
| AgentOpinion | Recommendation, confidence, conviction, evidence list, reasoning |
| CouncilDecision | Consensus direction, confidence, conviction, disagreement, tier |
| TradeSignal | Direction, confidence, conviction, stop loss, take profit |
| Trade | Entry/exit prices, PnL, direction, status, exit reason |

**Maturity:** Production-ready. Well-structured dataclasses with clear field definitions.

**Strengths:**
- Clean separation of concerns across schema types
- AgentOpinion includes an `evidence` list (primitive evidence tracking)
- Trade records include exit reasons (stop_loss, take_profit, time_expiry)
- Serialization/deserialization for persistence

**Weaknesses:**
- No Hypothesis schema — the central scientific object is absent
- Evidence in AgentOpinion is a flat list without direction, weight, source reliability, or decay
- No DecisionRecord schema — the complete scientific record does not exist
- No Knowledge schema
- No link between Trade (outcome) and the belief (hypothesis) that produced it
- Exit reasons are operational (stop_loss, take_profit) not scientific (wrong_hypothesis, wrong_timing)

**Scientific relevance:** Schemas define what the system can represent. The absence of Hypothesis, DecisionRecord, and Knowledge schemas means the system cannot represent its own learning.

---

#### Agents

| Component | Purpose |
|-----------|---------|
| MarketAgent | Technical analysis: RSI, SMA crossovers, ATR, volume, momentum |
| NewsAgent | Text/keyword analysis for news, geopolitical, regulatory events |
| MacroAgent | Macro indicator matching (GDP, CPI, Fed, recession) |
| RiskAgent | Volatility assessment, drawdown estimation, scenario risk |
| TrendAgent | EMA crossover trend follower |

**Maturity:** Working but architecturally frozen. All agents use static rules — none learn from outcomes.

**Strengths:**
- Each agent produces structured opinions with recommendation, confidence, evidence
- Agents cover different analytical domains (technical, news, macro, risk)
- Agent output feeds the Council correctly

**Weaknesses:**
- **All agents are frozen.** None adjust thresholds or rules based on performance.
- Agent opinions are not hypotheses — they lack invalidation conditions, time horizons, lifecycle states
- Evidence lists are unstructured (text strings, not weighted, attributed evidence items)
- No competing hypotheses are generated (each agent produces one opinion per event)
- Agent confidence is static — not calibrated against actual accuracy
- Agent cannot be wrong in a specific way — error is binary (recommendation was right or wrong)

**Scientific relevance:** Agents are the closest current approximation to Hypothesis formation. They interpret events and produce beliefs. But they produce opinions, not hypotheses. The gap is: opinions are static, hypotheses are testable.

---

#### Council

| Component | Purpose |
|-----------|---------|
| AgentCouncil | Weighted voting by agent track record, computes consensus and conviction |
| MetaCouncil | Cross-profile comparison (Trader, Entrepreneur, Creator) |

**Maturity:** Working. Track-record weighted voting is functional.

**Strengths:**
- Weighted voting by demonstrated agent accuracy
- Conviction computation from multiple dimensions
- Disagreement measurement (95% confidence intervals)
- Track record updates after each trade

**Weaknesses:**
- Council weights opinions, not hypotheses. There is no hypothesis to weigh.
- No competing hypothesis evaluation — the Council aggregates, it does not compete
- No hypothesis competition mechanism
- MetaCouncil is premature (profiles exist but only trading is operational)

**Scientific relevance:** The Council is the closest current approximation to the Decision object. It aggregates opinions and produces a decision. But in the object model, a Decision selects among competing hypotheses. The Council selects among agent opinions — a fundamentally different operation.

---

#### Execution

| Component | Purpose |
|-----------|---------|
| PaperTradingEngine | Simulated trade execution with position management |
| CapitalGuard | Capital protection: loss limits, drawdown, kill switch |
| CrashDetector | Multi-window crash detection |
| KnifeDetector | Distinguishes dip buys from falling knives |
| DirectionController | Disables long/short based on rolling win rate |
| GapRiskEngine | Overnight/weekend gap risk modeling |
| SlippageEngine | Spread and slippage simulation |
| PerformanceMemory | Agent track records, trade attribution, confidence bias |

**Maturity:** Production-ready. The execution layer is the most mature part of the MVP.

**Strengths:**
- Multiple guard layers operating correctly and independently
- Position management (open, monitor, close by SL/TP/time)
- Performance attribution per agent
- Confidence bias tracking (difference between confidence and accuracy)
- Robust error handling

**Weaknesses:**
- No link between trade (outcome) and hypothesis (belief that produced it)
- Exit reasons are operational, not scientific
- PerformanceMemory tracks agents, not hypotheses
- No error classification by decision type
- No comparison of outcome to expected scenario
- No knowledge extraction from outcomes

**Scientific relevance:** Execution produces Outcomes. PerformanceMemory produces primitive learning signals (agent accuracy). But outcomes are not compared to hypotheses, so they cannot produce Knowledge.

---

#### Memory and Database

| Component | Purpose |
|-----------|---------|
| OMACoreDatabase (SQLite) | Events, opportunities, user profiles |
| ShortTermMemory | TTL-based ephemeral storage (1 hour) |
| LongTermMemory | Tagged, persistent, access-count tracked |
| TelemetryRecorder | Append-only JSONL per cycle |

**Maturity:** Working but not designed for scientific record keeping.

**Strengths:**
- SQLite persistence for events and opportunities
- Telemetry captures full cycle logs
- Memory separation (short-term vs long-term)

**Weaknesses:**
- No hypothesis storage
- No knowledge storage
- No evidence tracking
- No DecisionRecord storage
- Telemetry is operational (timing, counts, errors) not scientific (hypotheses, evidence, decisions)
- Database cannot query by hypothesis, evidence quality, error type, or knowledge
- No immutability enforcement for scientific records

**Scientific relevance:** The current storage layer cannot represent the scientific objects. It stores events and trades but not the reasoning that connects them.

---

#### Monitoring

| Component | Purpose |
|-----------|---------|
| HealthMonitor | 10 checks for system integrity |
| FailureClassifier | Runtime exception classification (9 types) |

**Maturity:** Working for operational monitoring.

**Strengths:**
- Health checks catch operational anomalies
- FailureClassifier captures runtime errors with type classification

**Weaknesses:**
- HealthMonitor checks operational health, not scientific health
- FailureClassifier classifies runtime exceptions, not decision errors
- No criterion metrics tracking
- No calibration measurement
- No hypothesis quality trends
- No knowledge yield tracking

**Scientific relevance:** Current monitoring is operational. Scientific monitoring (criterion metrics, knowledge yield, calibration trends) does not exist.

---

#### CLI and Configuration

| Component | Purpose |
|-----------|---------|
| OMACLI | 9 commands for system operation |
| Config | Environment-based configuration dataclass |

**Maturity:** Working. Standard CLI with argparse.

**Weaknesses:**
- No commands for scientific operations (review hypotheses, examine knowledge, generate criterion reports)
- Configuration has no settings for hypothesis lifecycle, evidence thresholds, or research proposals

**Scientific relevance:** The CLI surface reflects the current MVP's purpose — operational trading. A Criterion Laboratory needs different interactions: research review, experiment design, knowledge browsing.

---

### 1.2 Component Maturity Summary

| Component | Operational | Scientific | Notes |
|-----------|-------------|------------|-------|
| Collectors | ✅ Mature | ❌ No evidence formation | Need hypothesis-linked evidence |
| Schemas (Event) | ✅ Mature | ❌ No Hypothesis, Knowledge, DecisionRecord | New schemas needed |
| Schemas (Agent) | ✅ Working | ❌ Not hypothesis-aware | AgentOpinion → Hypothesis |
| Schemas (Trade) | ✅ Mature | ❌ No hypothesis link | Need DecisionRecord |
| Agents | ✅ Working | ❌ Frozen, no learning | Need hypothesis formation capability |
| Council | ✅ Working | ⚠️ Partial | Decision exists but not hypothesis-selector |
| PaperTrading | ✅ Mature | ❌ No hypothesis comparison | Outcome exists but not science |
| Guards | ✅ Mature | ❌ Scientific relevance low | Not directly mapped to objects |
| PerformanceMemory | ✅ Working | ⚠️ Partial | Tracks agents, not hypotheses |
| Database | ✅ Working | ❌ No scientific storage | New tables needed |
| Memory (ST/LT) | ✅ Working | ❌ Not mapped to objects | Infrastructure only |
| Telemetry | ✅ Working | ❌ Operational, not scientific | Needs scientific record format |
| HealthMonitor | ✅ Working | ❌ No criterion metrics | New monitoring needed |
| FailureClassifier | ✅ Working | ⚠️ Partial | Runtime exceptions, not error types |

**Key finding:** The MVP is operationally mature but scientifically empty. Every component that touches learning (agents, council, performance memory, database) is missing the hypothesis layer that would make it scientific.

---

## PART II: Object Mapping

### 2.1 Mapping Current Components to Scientific Objects

```
Scientific Object           Current MVP Component(s)          Coverage
─────────────────           ──────────────────────────        ────────

Hypothesis                  AgentOpinion (primitive)           ❌ Missing
                            • has evidence list                  • no lifecycle
                            • has confidence                     • no invalidation conditions
                            • has recommendation                 • no time horizon
                                                                 • no competing hypotheses
                                                                 • no falsifiability

Evidence                    AgentOpinion.evidence list          ⚠️ Partial
                            • evidence exists as text strings    • no direction (supports/contradicts)
                            • no weighting                       • no source reliability
                            • no decay                           • no independence scoring

Decision                    CouncilDecision                     ⚠️ Partial
                            • choice with conviction             • not hypothesis-selector
                            • confidence computed                • no competing hypotheses considered
                            • reasoning captured                 • no expected scenario recorded
                                                                 • no decision quality evaluation

Outcome                     Trade                                ⚠️ Partial
                            • PnL recorded                       • no comparison to hypothesis
                            • exit reason recorded               • exit reasons are operational
                            • timing recorded                    • no error classification by decision type
                                                                 • no unexpected events captured

Knowledge                   PerformanceMemory (primitive)       ❌ Missing
                            • agent accuracy trends              • no knowledge extraction
                            • confidence bias                    • no generalizable lessons
                                                                 • no knowledge lifecycle
                                                                 • no knowledge application tracking

ResearchProposal            None                                ❌ Missing
                            • no equivalent exists              • no research question framing
                                                                 • no experiment design
                                                                 • no success/failure criteria

DecisionRecord              Telemetry (primitive)               ❌ Missing
                            • per-cycle JSONL logs               • no hypothesis, evidence, or knowledge
                            • operational data                   • no reflection
                                                                 • not queryable
                                                                 • not immutable
```

### 2.2 Duplicated Responsibilities

**Council and PerformanceMemory both track agent accuracy.** The Council updates agent track records after each trade. PerformanceMemory also tracks agent accuracy and confidence bias. These overlap. In the object model, DecisionRecord should be the single source of truth for outcome attribution.

**Database and LongTermMemory both store persistent data.** Database stores events and opportunities. LongTermMemory stores tagged entries. The boundary between them is unclear. In the object model, Scientific Memory (DecisionRecords) and Semantic Memory (Knowledge) will have clear separation.

**Telemetry and PerformanceMemory both record cycle data.** Telemetry logs every cycle. PerformanceMemory computes agent statistics from the same data. Both would be superseded by DecisionRecord as the primary scientific record.

### 2.3 Missing Responsibilities

| Responsibility | Missing From | Scientific Object |
|----------------|--------------|-------------------|
| Hypothesis creation with invalidation conditions | All components | Hypothesis |
| Hypothesis lifecycle state management | All components | Hypothesis |
| Competing hypothesis generation | All components | Hypothesis |
| Evidence tracking per hypothesis with direction/weight/decay | All components | Evidence |
| Source reliability tracking and updating | All components | Evidence |
| Decision-to-hypothesis linking | Council, PaperTrading | Decision |
| Expected scenario recording | Council | Decision |
| Outcome-to-hypothesis comparison | PaperTrading, PerformanceMemory | Outcome |
| Error classification by decision type | PerformanceMemory, FailureClassifier | Outcome |
| Knowledge extraction from outcomes | All components | Knowledge |
| Knowledge lifecycle management | All components | Knowledge |
| Research proposal generation | All components | ResearchProposal |
| Experiment design and tracking | All components | ResearchProposal |
| Criterion metrics computation | All components | DecisionRecord → CriterionSnapshot |
| Immutable scientific record storage | All components | DecisionRecord |

---

## PART III: Implementation Gap Analysis

### 3.1 Readiness Assessment per Scientific Object

```
Object: Hypothesis
───────────────────────────────────────────────────────────────────────
Already Exists:        ❌  No. AgentOpinion is a primitive approximation.
Partially Exists:      ⚠️  AgentOpinion has confidence, recommendation, evidence list.
Missing Completely:    ✅  Lifecycle states, invalidation conditions, time horizon,
                          falsifiability, competing alternatives, evidence inventory.
Needs Refactoring:     ⚠️  AgentOpinion → Hypothesis + Evidence.
Needs Replacement:     ✅  AgentOpinion must be replaced by Hypothesis.
Needs Nothing:         ❌  Everything must be built.
───────────────────────────────────────────────────────────────────────
Readiness: 5% (AgentOpinion evidence list can be reused)

Object: Evidence
───────────────────────────────────────────────────────────────────────
Already Exists:        ❌  No. Evidence lists exist but are unstructured text.
Partially Exists:      ⚠️  AgentOpinion.evidence list, collector source tracking.
Missing Completely:    ✅  Direction, weight, source reliability, decay,
                          independence scoring, per-hypothesis inventory.
Needs Refactoring:     ✅  Evidence strings → structured Evidence objects.
Needs Replacement:     ❌  N/A.
Needs Nothing:         ❌  Everything must be built.
───────────────────────────────────────────────────────────────────────
Readiness: 10% (raw evidence strings exist)

Object: Decision
───────────────────────────────────────────────────────────────────────
Already Exists:        ⚠️  CouncilDecision has choice, confidence, conviction.
Partially Exists:      ✅  CouncilDecision, TradeSignal exist with useful fields.
Missing Completely:    ✅  Hypothesis selection, competing alternatives,
                          expected scenario, decision quality evaluation.
Needs Refactoring:     ⚠️  CouncilDecision → Decision (new fields, new links).
Needs Replacement:     ❌  N/A.
Needs Nothing:         ❌  Must be extended.
───────────────────────────────────────────────────────────────────────
Readiness: 40% (CouncilDecision is closest to scientific Decision)

Object: Outcome
───────────────────────────────────────────────────────────────────────
Already Exists:        ⚠️  Trade has PnL, entry/exit, exit reason.
Partially Exists:      ✅  Trade, exit reason, timing data exist.
Missing Completely:    ✅  Hypothesis comparison, error classification,
                          unexpected events, outcome vs. prediction.
Needs Refactoring:     ⚠️  Trade → Outcome (new fields, link to hypothesis).
Needs Replacement:     ❌  N/A.
Needs Nothing:         ❌  Must be extended.
───────────────────────────────────────────────────────────────────────
Readiness: 50% (Trade is closest to scientific Outcome)

Object: Knowledge
───────────────────────────────────────────────────────────────────────
Already Exists:        ❌  No. PerformanceMemory computes statistics, not knowledge.
Partially Exists:      ⚠️  PerformanceMemory has agent accuracy, confidence bias.
Missing Completely:    ✅  Knowledge extraction, generalization, lifecycle,
                          application tracking, invalidation.
Needs Refactoring:     ❌  N/A — must be built from nothing.
Needs Replacement:     ❌  N/A.
Needs Nothing:         ❌  Everything must be built.
───────────────────────────────────────────────────────────────────────
Readiness: 0%

Object: ResearchProposal
───────────────────────────────────────────────────────────────────────
Already Exists:        ❌  No. No equivalent exists in any form.
Partially Exists:      ❌  Nothing.
Missing Completely:    ✅  Everything.
Needs Refactoring:     ❌  N/A — must be built from nothing.
Needs Replacement:     ❌  N/A.
Needs Nothing:         ❌  Everything must be built.
───────────────────────────────────────────────────────────────────────
Readiness: 0%

Object: DecisionRecord
───────────────────────────────────────────────────────────────────────
Already Exists:        ❌  No. Telemetry captures operational data only.
Partially Exists:      ⚠️  Telemetry JSONL logs per cycle, Trade records.
Missing Completely:    ✅  Scientific content, immutability, queryability,
                          hypothesis-evidence-decision-outcome-knowledge bundle.
Needs Refactoring:     ✅  Telemetry → DecisionRecord (new schema, new storage).
Needs Replacement:     ❌  N/A.
Needs Nothing:         ❌  Must be built.
───────────────────────────────────────────────────────────────────────
Readiness: 5% (Telemetry structure can be repurposed)
```

### 3.2 Overall Readiness

| Object | Readiness | Effort Estimate | Dependencies |
|--------|-----------|-----------------|--------------|
| Hypothesis | 5% | Very High | New schema, lifecycle, generation mechanism |
| Evidence | 10% | Medium | Hypothesis must exist first |
| Decision | 40% | Low-Medium | Extend existing CouncilDecision |
| Outcome | 50% | Low | Extend existing Trade |
| Knowledge | 0% | High | Hypothesis, Decision, Outcome must exist |
| ResearchProposal | 0% | Medium | Knowledge must exist (proposals address gaps) |
| DecisionRecord | 5% | Medium | All other objects must exist |

**The system is not ready for implementation until the Hypothesis object exists.** Hypothesis is the central object — everything else depends on it. Building Evidence, Decision, Outcome, or Knowledge without Hypothesis is building components for a machine that has no engine.

---

## PART IV: Engineering Priorities

### 4.1 Priority Principle

Every priority is determined by three factors:

1. **Scientific value** — How much does this contribute to the project's ability to produce evidence of criterion development?
2. **Engineering effort** — How much existing code can be reused? How much must be built from scratch?
3. **Future leverage** — Does this unlock other improvements? Or is it a dead end?

Priorities are ordered by **scientific value per unit of engineering effort** in a way that maximizes future leverage.

### 4.2 Priority Rankings

```
Priority 1: Hypothesis Schema + Lifecycle
────────────────────────────────────────────
Scientific value:  Critical — without hypotheses, no learning is possible
Engineering effort: High — new schema, new state machine, new persistence
Future leverage:    Maximum — every other object depends on Hypothesis
Existing code:      AgentOpinion schema can inform Hypothesis fields
Dependencies:       None (foundational)
────────────────────────────────────────────

Priority 2: Evidence as Structured Object
────────────────────────────────────────────
Scientific value:  Critical — without evidence, hypotheses are speculation
Engineering effort: Medium — schema change, link to Hypothesis
Future leverage:    High — evidence quality feeds Knowledge and Criterion
Existing code:      AgentOpinion.evidence list provides starting data
Dependencies:       Priority 1 (Hypothesis must exist first)
────────────────────────────────────────────

Priority 3: Decision → Hypothesis Linking
────────────────────────────────────────────
Scientific value:  High — without this link, outcomes cannot be traced to beliefs
Engineering effort: Low-Medium — extend CouncilDecision with hypothesis_id
Future leverage:    High — enables all outcome analysis
Existing code:      CouncilDecision, TradeSignal exist
Dependencies:       Priority 1 (Hypothesis must exist)
────────────────────────────────────────────

Priority 4: Outcome → Hypothesis Comparison
────────────────────────────────────────────
Scientific value:  High — this is the core learning signal
Engineering effort: Medium — extend Trade with hypothesis_id, comparison logic
Future leverage:    High — enables error classification
Existing code:      Trade, PerformanceMemory exist
Dependencies:       Priority 3 (hypothesis-linked decisions)
────────────────────────────────────────────

Priority 5: Error Classification by Decision Type
────────────────────────────────────────────
Scientific value:  High — enables learning from failure
Engineering effort: Medium — new taxonomy, classification logic
Future leverage:    High — enables Knowledge extraction
Existing code:      FailureClassifier provides pattern for classification
Dependencies:       Priority 4 (outcome comparison exists)
────────────────────────────────────────────

Priority 6: DecisionRecord Schema + Storage
────────────────────────────────────────────
Scientific value:  High — enables scientific record keeping
Engineering effort: Medium — new aggregate, new storage layer
Future leverage:    High — enables CriterionSnapshot computation
Existing code:      Telemetry provides logging pattern
Dependencies:       Priorities 1–5 (all objects must exist)
────────────────────────────────────────────

Priority 7: Knowledge Extraction from DecisionRecords
────────────────────────────────────────────
Scientific value:  Critical — this is the output of learning
Engineering effort: High — new object, new extraction logic, new lifecycle
Future leverage:    High — knowledge feeds criterion directly
Existing code:      PerformanceMemory reports provide pattern
Dependencies:       Priority 6 (DecisionRecord must exist)
────────────────────────────────────────────

Priority 8: CriterionSnapshot Computation
────────────────────────────────────────────
Scientific value:  Critical — without measurement, criterion is philosophical
Engineering effort: Medium — aggregation queries, trend analysis
Future leverage:    High — enables autonomy decisions
Existing code:      PerformanceMemory metrics provide pattern
Dependencies:       Priority 7 (Knowledge must exist)
────────────────────────────────────────────

Priority 9: ResearchProposal
────────────────────────────────────────────
Scientific value:  Medium-High — ensures experiments have purpose
Engineering effort: Low-Medium — new schema, lifecycle, linking
Future leverage:    Medium — prevents hypothesis proliferation
Existing code:      None — must be built
Dependencies:       Priority 8 (criterion gaps inform proposals)
────────────────────────────────────────────
```

### 4.3 Why This Order

**Hypothesis first.** The system currently has no unit of learning. Building anything else first would be building infrastructure for a process that does not exist. The hypothesis is the engine.

**Evidence second.** A hypothesis without evidence is an opinion. The system can form hypotheses, but without structured evidence tracking, hypothesis quality cannot improve. Evidence gives hypotheses their scientific content.

**Decision-Hypothesis link third.** Before this link exists, every decision exists in isolation. After this link, every decision can be traced to the belief that produced it. This is the prerequisite for all learning.

**Outcome comparison fourth.** Before this exists, outcomes are just numbers. After this, every outcome confirms or rejects a hypothesis. This is the learning signal.

**Error classification fifth.** Before this, failures are indistinguishable. After this, the system can learn from different failure modes differently. This is the mechanism for targeted improvement.

**DecisionRecord sixth.** Before this, scientific records are scattered across multiple stores. After this, every cycle produces a complete, immutable scientific record. This enables all higher-level analysis.

**Knowledge extraction seventh.** Before this, learning is implicit. After this, the system produces explicit, generalizable lessons. This is the bridge between individual outcomes and accumulated criterion.

**CriterionSnapshot eighth.** Before this, criterion is philosophical. After this, it is measurable. This is the evidence the project exists to produce.

**ResearchProposal ninth.** Before this, experiments exist without scientific framing. After this, every experiment belongs to a research program. This ensures the system does not generate hypotheses without purpose.

---

## PART V: The First Implementation Iterations

### 5.1 Iteration Design Principles

- Every iteration must be **independently testable** — it can be verified in isolation before the next iteration begins
- Every iteration must **preserve existing functionality** — the current event-to-trade pipeline continues working
- Every iteration must **produce evidence** — even incomplete iterations should enable better measurement than the current system
- Iterations are ordered by the priority sequence from Part IV

### 5.2 Iteration 1: Hypothesis Foundation

**Objective.** Make Hypothesis a first-class object in the system. A hypothesis can be created with required attributes, tracked through a lifecycle, and linked to the events that triggered it.

**Objects affected:** Hypothesis

**What must be built:**
- Hypothesis data structure with: ID, title, description, predicted consequence, time horizon, invalidation conditions, context scope, confidence, current status, status history
- Hypothesis lifecycle state machine (CANDIDATE → FORMULATED → ACTIVE → EVALUATED → CONFIRMED/REJECTED/INCONCLUSIVE → ARCHIVED)
- Hypothesis persistence (new database table or document store)
- Hypothesis creation mechanism (at minimum: manual creation via CLI; seeds the pipeline)
- Hypothesis querying (list by status, by domain, by confidence)

**What is preserved from MVP:**
- All collectors continue working
- All agents continue producing opinions
- All execution and guard layers continue operating
- Existing schemas remain unchanged

**Integration with MVP:**
- During Iteration 1, hypotheses are created independently of the operational pipeline. They are not yet linked to trades.
- The system can create hypotheses, track their state, and archive them. This is the foundation.

**Expected evidence:**
- A hypothesis can be created with all required fields
- A hypothesis transitions through its lifecycle correctly
- A hypothesis can be queried by status, domain, and confidence
- Hypotheses can be archived and preserved

**Success criteria:**
- Hypothesis CRUD operations work correctly
- State machine transitions are recorded with timestamps
- At least 10 hypotheses can be created, tracked, and archived

**Testability:** Unit tests for hypothesis lifecycle. Integration test for creation → active → archived flow.

---

### 5.3 Iteration 2: Evidence Tracking

**Objective.** Evidence becomes a structured object linked to a hypothesis. Evidence has direction, weight, source reliability, and decay. A hypothesis maintains an evidence inventory.

**Objects affected:** Hypothesis (extended), Evidence (new)

**What must be built:**
- Evidence data structure with: ID, hypothesis_id, direction (supports/contradicts), weight, source_id, source_reliability, timestamp, independence_score
- Source reliability tracking (source_id → reliability_score, updated over time)
- Evidence inventory per hypothesis (supporting and contradicting tracked separately)
- Evidence decay mechanism (time-based or event-based)
- Evidence collection mechanism (at minimum: evidence can be added to a hypothesis via CLI or automated collector)

**What is preserved from MVP:**
- Agent opinions continue to include evidence lists (these become raw material for structured Evidence)
- All existing pipeline continues

**Integration with MVP:**
- Agent opinion evidence lists are parsed into structured Evidence objects
- Collectors become evidence sources with tracked reliability
- Each collector's source_id is registered with initial reliability = 1.0

**Expected evidence:**
- Evidence can be created, linked to a hypothesis, and queried
- Evidence direction and weight are tracked independently
- Evidence source reliability updates over time
- Evidence decays correctly

**Success criteria:**
- Evidence CRUD operations work correctly
- Supporting and contradicting evidence are tracked as separate dimensions
- Source reliability updates after each outcome
- Evidence decay function produces correct expiration

**Testability:** Unit tests for evidence lifecycle. Integration test for evidence collection → decay flow.

---

### 5.4 Iteration 3: Hypothesis-Linked Decisions

**Objective.** Every decision is linked to the hypothesis it was based on. The system records which hypothesis was chosen, what alternatives were considered, and the expected scenario at decision time.

**Objects affected:** Decision, Hypothesis (extended with decision link)

**What must be built:**
- Decision schema extended with: hypothesis_id, competing_hypotheses_ids, expected_scenario, contradictory_scenario, decision_quality_score (retrospective)
- CouncilDecision → Decision mapping: CouncilDecision becomes a Decision with a hypothesis link
- Decision record persistence (new table or extended council table)
- Execution chain extended: Decision creation → hypothesis link → outcome waiting

**What is preserved from MVP:**
- CouncilDecision continues to function
- PaperTradingEngine continues to execute
- Guard layers continue to protect

**Integration with MVP:**
- AgentCouncil creates a Decision (not just a CouncilDecision) that references the chosen hypothesis
- The Decision carries forward into PaperTradingEngine instead of CouncilDecision
- Guard modifications are recorded on the Decision (not discarded)

**Expected evidence:**
- Every decision can be traced to the hypothesis that produced it
- Competing hypotheses are recorded alongside the chosen one
- Expected scenario is recorded before outcome is known
- Decision quality can be evaluated retrospectively (given evidence at decision time)

**Success criteria:**
- Every decision in the system carries a hypothesis_id
- Competing hypotheses are recorded (at minimum: "no alternatives considered" as a placeholder)
- At least 10 decisions with complete hypothesis linkage exist

**Testability:** Integration test tracing a full cycle: hypothesis → decision → action → outcome record.

---

### 5.5 Iteration 4: Outcome Comparison

**Objective.** Every outcome is compared to the hypothesis that produced it. The system records whether the hypothesis was confirmed, rejected, or inconclusive, and classifies errors by type.

**Objects affected:** Outcome, Hypothesis (receives verdict), ErrorType

**What must be built:**
- Outcome schema extended with: hypothesis_id, hypothesis_verdict (CONFIRMED/REJECTED/INCONCLUSIVE), error_type, error_severity, unexpected_events
- Hypothesis verdict assignment logic: compare outcome to prediction within tolerance
- ErrorType taxonomy (WRONG_EVENT_INTERPRETATION, WRONG_CORRELATION, WRONG_CONSEQUENCE, CORRECT_CONSEQUENCE_WRONG_TIMING, CORRECT_HYPOTHESIS_POOR_EXECUTION, EXTERNAL_SHOCK, CORRECT_OUTCOME)
- Error classification assignment logic (at minimum: human-in-the-loop or rule-based)
- PerformanceMemory migration: agent accuracy tracking continues but now references hypothesis outcomes

**What is preserved from MVP:**
- Trade records continue to be created
- Exit reasons continue to be recorded
- PerformanceMemory continues to compute agent statistics

**Integration with MVP:**
- When a trade closes, PaperTradingEngine triggers outcome comparison
- Trade PnL is compared to the hypothesis's predicted consequence
- Error type is assigned based on the comparison result
- PerformanceMemory reads from hypothesis outcomes, not raw trades

**Expected evidence:**
- Each outcome carries a hypothesis verdict
- Error types are assigned to rejected hypotheses
- The system can report: "X hypotheses confirmed, Y rejected, Z inconclusive"
- Error type frequency distribution is available

**Success criteria:**
- 90%+ of closed trades carry a hypothesis verdict
- Error type assignment is consistent (inter-rater reliability > 0.8 if human-in-the-loop)
- Error type frequency report can be generated

**Testability:** Integration test: trade closes → hypothesis comparison → verdict assignment → error classification.

---

### 5.6 Iteration 5: DecisionRecord

**Objective.** Every operational cycle produces a complete, immutable DecisionRecord that bundles hypothesis, evidence, decision, outcome, reflection, and knowledge. DecisionRecords become the single source of truth for all scientific analysis.

**Objects affected:** DecisionRecord (aggregate), all prior objects (now linked through DecisionRecord)

**What must be built:**
- DecisionRecord schema bundling: hypothesis_id, evidence_ids, decision_id, outcome_id, reflection (embedded), knowledge_ids
- DecisionRecord lifecycle (OPEN → COMPLETED → ANALYZED → ARCHIVED)
- DecisionRecord storage (immutable, append-only, queryable)
- Reflection schema: outcome_vs_prediction, error_type, error_severity, unexpected_events, lessons_preliminary, confidence_calibration_note
- DecisionRecord query layer (search by hypothesis type, error type, verdict, confidence range, date range)

**What is preserved from MVP:**
- Telemetry continues to log operational data (parallel to DecisionRecord)
- All existing data remains accessible

**Integration with MVP:**
- Telemetry → DecisionRecord: Telemetry provides operational data; DecisionRecord provides scientific content
- At cycle completion, a DecisionRecord is assembled from: hypothesis (from Hypothesis), evidence (from Evidence store), decision (from Council), outcome (from Trade), reflection (from comparison step)
- DecisionRecord is written to scientific memory (immutable store)

**Expected evidence:**
- Complete DecisionRecords exist for every operational cycle
- DecisionRecords are queryable by any scientific dimension
- No DecisionRecord is modified after creation
- DecisionRecords can be aggregated for criterion analysis

**Success criteria:**
- 100% of operational cycles produce a DecisionRecord
- DecisionRecords are immutable (append-only store verified)
- Queries by hypothesis type, error type, and verdict return correct results
- At least 10 completed DecisionRecords exist

**Testability:** Unit tests for DecisionRecord assembly. Integration test for full cycle → complete DecisionRecord.

---

### 5.7 Iteration 6: Knowledge Extraction

**Objective.** Knowledge is extracted from DecisionRecords. Every confirmed or rejected hypothesis produces at least one generalizable lesson. Knowledge has its own lifecycle and feeds future hypothesis formation.

**Objects affected:** Knowledge (new), DecisionRecord (extended with knowledge extraction)

**What must be built:**
- Knowledge data structure with: ID, statement (the lesson), source_decisionrecord_ids, conditions (context/regime where applicable), confidence, status (PROVISIONAL → VALIDATED / REVISED / INVALIDATED → ARCHIVED), created_at, last_applied_at
- Knowledge extraction mechanism (at minimum: rule-based templates or human review)
- Knowledge application tracking (which hypotheses were informed by which knowledge)
- Knowledge lifecycle management (extracted → provisional → validated/rejected)
- Knowledge querying (by domain, by conditions, by confidence, by source hypothesis type)

**What is preserved from MVP:**
- PerformanceMemory continues to provide agent-level statistics
- All existing pipeline continues

**Integration with MVP:**
- After a DecisionRecord is completed and analyzed, Knowledge extraction runs
- Extracted knowledge is stored in semantic memory
- Knowledge with high confidence can inform future hypothesis formation
- Hypothesis creation can reference relevant knowledge

**Expected evidence:**
- Each DecisionRecord produces at least one Knowledge entry
- Knowledge entries are linked to their source hypotheses
- Knowledge can be queried by conditions and domain
- Knowledge lifecycle transitions are recorded

**Success criteria:**
- 70%+ of DecisionRecords produce at least one knowledge entry
- Knowledge entries are queryable
- At least 5 knowledge entries reach VALIDATED status
- Validation criteria for knowledge are documented

**Testability:** Unit tests for Knowledge lifecycle. Integration test: DecisionRecord → Knowledge extraction → Knowledge storage.

---

### 5.8 Iteration 7: CriterionSnapshot

**Objective.** Criterion metrics are computed periodically from DecisionRecords. The system can measure whether its judgment is improving over time.

**Objects affected:** CriterionSnapshot (computed view), DecisionRecord (data source)

**What must be built:**
- CriterionSnapshot computation engine (aggregates DecisionRecords over a window)
- Metric dimensions: hypothesis quality, evidence quality, calibration, error recurrence rate, knowledge yield, learning velocity, decision utility
- Trend analysis: compare current snapshot to previous snapshots
- Criterion report generation (structured output for review)
- Alert thresholds: degradation detection (statistically significant negative trends)

**What is preserved from MVP:**
- HealthMonitor continues operational monitoring
- All existing pipeline continues

**Integration with MVP:**
- CriterionSnapshot reads from DecisionRecords in scientific memory
- Periodic computation (e.g., weekly, after every N DecisionRecords)
- Results are stored alongside DecisionRecords (derived data, not independently mutable)

**Expected evidence:**
- Criterion metrics can be computed from completed DecisionRecords
- Trends can be detected across multiple snapshots
- Calibration can be measured (if sufficient data exists per confidence bucket)
- Error type frequency trends are visible

**Success criteria:**
- Minimum 30 DecisionRecords required for first meaningful snapshot
- At least 3 of 7 metric dimensions show stable or improving trends after 90 days
- Calibration measurement is possible (minimum 5 data points per confidence bucket)

**Testability:** Integration test: DecisionRecords → CriterionSnapshot computation → trend analysis.

---

### 5.9 Iteration 8: ResearchProposal

**Objective.** Every experiment is framed by a research proposal. The system generates proposals from criterion gaps and tracks their completion.

**Objects affected:** ResearchProposal (new), DecisionRecord (extended with proposal link)

**What must be built:**
- ResearchProposal data structure with: ID, research_question, hypothesis_to_test, expected_impact, success_criteria, failure_criteria, status (DRAFT → ACTIVE → EVALUATING → CONFIRMED/REJECTED/INCONCLUSIVE → ARCHIVED)
- ResearchProposal → DecisionRecord linking (each record belongs to a proposal)
- Proposal generation mechanism (at minimum: manual creation; automated from criterion gaps is aspirational)
- Proposal tracking (how many DecisionRecords, what knowledge was produced, was the hypothesis confirmed/rejected?)

**What is preserved from MVP:**
- All existing pipeline continues

**Integration with MVP:**
- Before a hypothesis is created, a ResearchProposal must exist (or an "Exploratory Investigation" default)
- DecisionRecords reference their parent proposal
- When a proposal concludes, its findings are documented

**Expected evidence:**
- Every DecisionRecord belongs to a ResearchProposal
- Proposals have clear success/failure criteria
- Completed proposals document what was learned
- Criterion gaps trigger new proposals

**Success criteria:**
- 100% of DecisionRecords belong to a ResearchProposal (including "Exploratory" default)
- At least 3 proposals completed with documented findings
- Proposal findings reference the knowledge they produced

**Testability:** Integration test: ResearchProposal → multiple DecisionRecords → proposal completion analysis.

---

### 5.10 Iteration Summary

| Iteration | Objective | Dependencies | Scientific Value | Existing Code Leverage |
|-----------|-----------|--------------|------------------|----------------------|
| 1 | Hypothesis Foundation | None | Critical | 5% (AgentOpinion) |
| 2 | Evidence Tracking | 1 | Critical | 10% (evidence strings) |
| 3 | Hypothesis-Linked Decisions | 1 | High | 40% (CouncilDecision) |
| 4 | Outcome Comparison | 1, 3 | High | 50% (Trade) |
| 5 | DecisionRecord | 1, 2, 3, 4 | High | 5% (Telemetry) |
| 6 | Knowledge Extraction | 5 | Critical | 0% |
| 7 | CriterionSnapshot | 5 | Critical | 0% (new computation) |
| 8 | ResearchProposal | 7 | Medium-High | 0% |

**Total iterations: 8**

---

## PART VI: Traceability Matrix

### 6.1 The Chain of Justification

No engineering work may exist without a chain of justification tracing back to a scientific need.

```
Research Proposal
    ↓  (identifies a gap in criterion)
Scientific Question
    ↓  (frames what must be known)
Hypothesis
    ↓  (proposes a testable answer)
Scientific Object
    ↓  (the object that represents this concept)
Engineering Task
    ↓  (what must be built or changed)
Validation Method
    ↓  (how we know it works)
Expected Criterion Improvement
    ↓  (how the system's judgment should improve)
Evidence
```

### 6.2 Example: Hypothesis Lifecycle

| Layer | Content |
|-------|---------|
| **Research Proposal** | RP-001: "Does explicit hypothesis tracking improve decision traceability?" |
| **Scientific Question** | "Can the system form testable, falsifiable beliefs and track them through a defined lifecycle?" |
| **Hypothesis** | "A system that tracks hypotheses through a lifecycle will produce decision records that can be traced to the beliefs that produced them." |
| **Scientific Object** | Hypothesis (02_SCIENTIFIC_OBJECT_MODEL.md — Object 1) |
| **Engineering Task** | IT-01: Implement Hypothesis schema with lifecycle state machine (Iteration 1) |
| **Validation Method** | Unit tests: hypothesis creation, state transitions, archiving. Integration test: hypothesis survives full lifecycle. |
| **Expected Criterion Improvement** | Decision traceability: from 0% (currently no hypothesis exists) to 100% (every decision has a hypothesis). Hypothesis Quality metric becomes measurable. |

### 6.3 Full Traceability Matrix

```
Scientific Object    → Engineering Iteration   → Validation Method              → Criterion Dimension
─────────────────      ─────────────────────     ──────────────────────────       ─────────────────────
Hypothesis             IT-01: Schema + State     Unit: lifecycle transitions      Hypothesis Quality
                       Machine                   Integ: full lifecycle flow

Evidence               IT-02: Structured          Unit: direction, weight,         Evidence Quality
                       Evidence                  decay correctness
                                                 Integ: evidence → hypothesis
                                                 link

Decision               IT-03: Hypothesis Link     Unit: decision-hypothesis        Decision Utility
                                                 association
                                                 Integ: decision traces to
                                                 hypothesis

Outcome                IT-04: Verdict +           Unit: verdict assignment          Error Classification
                       Error Classification       Integ: trade close → verdict      Error Recurrence Rate

DecisionRecord         IT-05: Aggregate           Unit: assembly correctness        All dimensions
                       + Immutable Storage        Integ: complete cycle → record   (data source)

Knowledge              IT-06: Extraction          Unit: knowledge lifecycle         Knowledge Yield
                       + Lifecycle               Integ: DecisionRecord →           Learning Velocity
                                                 Knowledge

CriterionSnapshot      IT-07: Computation         Integ: DecisionRecords →          Calibration
                       + Trend Analysis           Criterion dimensions              All trend dimensions

ResearchProposal       IT-08: Schema + Link       Unit: proposal lifecycle          Research Direction
                                                  Integ: proposal → DecisionRecord → findings
```

### 6.4 What This Prevents

The traceability matrix prevents:
- **Orphan engineering** — code that exists without scientific justification
- **Premature optimization** — building infrastructure before the concepts it serves exist
- **Scope creep** — adding features that do not trace to a criterion dimension
- **Unvalidated changes** — modifying components without a validation method
- **Lost justification** — six months later, no one remembers why something was built

---

## PART VII: What Must Never Change

### 7.1 Architectural Invariants

These principles are untouchable. They survive every iteration, every refactoring, every technology migration. They define what O.M.A.-C.O.R.E. is.

---

**Invariant 1 — Evidence First.**

No claim about system behavior, performance, or improvement is accepted without evidence. Evidence is stored, traceable, and independently verifiable. The system does not trust its own intuition — it trusts its recorded observations.

This is untouchable because it is the project's core scientific commitment. Violating it would make the project indistinguishable from any system that claims improvement without proof.

---

**Invariant 2 — Hypothesis Driven.**

Every action is traceable to a testable, falsifiable hypothesis. If there is no hypothesis, there is no learning. If there is no learning, the action produced a data point but not knowledge.

This is untouchable because the hypothesis is the unit of learning. Without it, the system cannot improve in a measurable, attributable way.

---

**Invariant 3 — Decision Traceability.**

Every decision can be traced to the hypothesis, evidence, and confidence that produced it. Decisions are recorded before outcomes are known. This prevents hindsight bias in evaluation.

This is untouchable because it is the only way to distinguish skill from luck. Without it, the system learns superstitions.

---

**Invariant 4 — Criterion Emergence.**

Criterion is never a component, engine, or module. It is not built. It emerges from the interaction of hypotheses, evidence, decisions, outcomes, reflection, and knowledge over time. No single piece of code produces criterion.

This is untouchable because believing criterion can be built directly would lead to building the wrong thing.

---

**Invariant 5 — Scientific Validation.**

Every improvement claim must be validated through the five-layer hierarchy: reasoning → decision → execution → outcome → learning. No single metric is sufficient. Converging evidence across layers is required.

This is untouchable because any single metric can be gamed. Only converging evidence prevents self-deception.

---

**Invariant 6 — Explicit Learning.**

Learning is explicit, recorded, and measurable. Knowledge is extracted, stored, and applied. Implicit learning (weight adjustments, model drift) is not learning — it is adaptation. The system does both, but only explicit learning counts as criterion development.

This is untouchable because implicit learning cannot be inspected, challenged, or validated.

---

**Invariant 7 — Minimal Complexity.**

Every component, layer, and abstraction must justify its existence. Complexity is debt. The default answer to any proposed addition is no. The burden of proof is on the proposer.

This is untouchable because complexity is the primary risk to long-term maintainability.

---

**Invariant 8 — Long-Term Maintainability.**

Every architecture decision is evaluated against the question: "Will this still make sense in ten years?" If the answer is unclear, simplify. Dependencies must be replaceable. The philosophy must survive the implementation.

This is untouchable because the project's value compounds over decades. Short-term optimizations that degrade long-term maintainability are not optimizations.

---

### 7.2 What Can Change

Everything else can change:
- Programming languages
- Frameworks
- Database technology
- API design
- UI/CLI interfaces
- Deployment infrastructure
- Specific metric formulas
- Evidence decay functions
- Hypothesis state names
- Error type taxonomy
- Knowledge extraction methods

The objects can evolve (new attributes, refined lifecycles). But the eight invariants above are constraints on how they evolve.

---

## PART VIII: Implementation Risks

### 8.1 Technical Risks

| Risk | Probability | Impact | Detection | Mitigation |
|------|-------------|--------|-----------|------------|
| **Hypothesis lifecycle cannot be retrofitted cleanly** | Medium | High — existing pipeline may resist hypothesis integration | When Iteration 3 attempts to link decisions to hypotheses | Add hypothesis_id fields to existing schemas first (low-risk); test integration before building full lifecycle |
| **PerformanceMemory migration loses historical data** | Medium | Medium — loss of agent accuracy history | During Iteration 4 migration | Keep PerformanceMemory running in parallel. Migrate after verifying hypothesis-based tracking produces equivalent results. |
| **Scientific record storage becomes too slow for operational cycles** | Low-Medium | Medium — operational tempo drops | During Iteration 5, when DecisionRecords are written per cycle | Use asynchronous write for DecisionRecords; operational path does not wait for scientific memory |
| **Knowledge extraction cannot be automated** | High | High — extraction requires human-in-the-loop indefinitely | During Iteration 6 | Start with template-based extraction (structured fields, automated). Add human review as optional enrichment, not required gate. |

### 8.2 Scientific Risks

| Risk | Probability | Impact | Detection | Mitigation |
|------|-------------|--------|-----------|------------|
| **Hypothesis lifecycle does not improve decision quality** (A-007) | Medium | Critical — core assumption falsified | After Iteration 7, when CriterionSnapshot trends can be measured | Document this as the central falsification condition. If no improvement after 12 months, abandon the lifecycle approach. |
| **Criterion metrics do not converge with trading metrics** | Medium | High — criterion improvement does not produce profits | After 6+ months of CriterionSnapshot data | Investigate whether criterion is the wrong goal or metrics are measuring the wrong dimensions. Adjust metrics, not mission. |
| **Evidence tracking adds overhead without improving calibration** | Medium | Medium — complexity not justified | After Iteration 2, compare calibration with and without structured evidence | Simplify evidence to essential dimensions only. Remove dimensions that do not improve calibration. |
| **Error classification cannot be consistent** | Medium | Medium — taxonomy produces ambiguous classifications | During Iteration 4, when error types are assigned | Start with 3 broad categories (hypothesis error, timing error, execution error). Expand only when data shows finer granularity is useful. |

### 8.3 Architectural Risks

| Risk | Probability | Impact | Detection | Mitigation |
|------|-------------|--------|-----------|------------|
| **Three-memory architecture is too complex** | Medium | Medium — maintenance burden outweighs benefit | During Iteration 5, when DecisionRecord storage is implemented | Start with two memories: immutable scientific record (DecisionRecords) + updatable semantic memory (Knowledge). Operational memory is the existing database. |
| **DecisionRecord becomes a performance bottleneck** | Low-Medium | Medium — cycles slowed by record assembly | During Iteration 5, under load testing | Assemble DecisionRecords asynchronously. Operational path does not wait for scientific record to be written. |
| **Object model does not map cleanly to existing database** | Medium | Medium — impedance mismatch between objects and relational tables | During Iteration 1, when Hypothesis schema is designed | Consider document storage for scientific objects. The object model is not relational — forcing it into normalized tables may add complexity without benefit. |

### 8.4 Complexity Risks

| Risk | Probability | Impact | Detection | Mitigation |
|------|-------------|--------|-----------|------------|
| **Eight iterations introduce too many changes for the codebase to absorb** | High | Medium — instability, regressions, cognitive overload | During any iteration deployment | Each iteration must be independently testable and deployable. No iteration depends on the next. The system continues operating between iterations. |
| **Each iteration adds new schemas, tables, and state machines without removing old ones** | Medium-High | Medium — accumulation of unused code | During code review | Each iteration should remove or deprecate the equivalent of what it adds. When Hypothesis is created, AgentOpinion is not removed — but it is no longer the primary representation. |

### 8.5 Human Risks

| Risk | Probability | Impact | Detection | Mitigation |
|------|-------------|--------|-----------|------------|
| **Developers bypass the hypothesis lifecycle for speed** | Medium | High — system reverts to signal engine | During code review, when trades are executed without hypothesis links | Enforce hypothesis_id as required field at the schema level. A decision without a hypothesis_id should fail validation. |
| **Complexity is added faster than it is justified** | High | Medium — conceptual debt accumulates | During retrospective review | Enforce the traceability matrix. Every component must trace to a scientific object and a criterion dimension. |
| **Scientific rigor is abandoned under time pressure** | Medium | High — evidence quality degrades | During CriterionSnapshot analysis, when metrics degrade | The invariants (Part VII) are not negotiable. If pressure is high, reduce scope, not rigor. |

---

## PART IX: Definition of Implementation Ready

### 9.1 The MVP Is Not Implementation Ready Simply Because Code Exists

The current MVP has ~12,000 lines of working Python code. It runs. It trades. It records outcomes.

It is not ready for ERA II implementation.

Implementation readiness is not determined by how much code exists. It is determined by how precisely the target is defined.

### 9.2 Conditions for Implementation to Begin

Implementation of any ERA II feature must satisfy these conditions:

---

**Condition 1 — The Scientific Object is defined.**

The object must be defined in 02_SCIENTIFIC_OBJECT_MODEL.md with:
- Clear purpose
- Operational definition
- Inputs and outputs
- Responsibilities
- Lifecycle
- Relationships to other objects
- Evidence required for its creation

*A component whose object definition is incomplete is not ready for implementation.*

---

**Condition 2 — The Traceability Chain exists.**

The implementation must trace:
- Research Proposal → Scientific Question → Hypothesis → Object → Engineering Task → Validation Method → Expected Criterion Improvement

*Code without a traceability chain is speculative engineering.*

---

**Condition 3 — The existing component is understood.**

Before modifying any MVP component, its current behavior must be documented:
- What does it do?
- What are its inputs and outputs?
- What are its current consumers?
- What would break if it changed?

*A component modified without this understanding introduces regression risk.*

---

**Condition 4 — The success criteria are measurable.**

Every implementation iteration must define:
- What constitutes success
- How success is measured
- What data is required for measurement
- What threshold constitutes "pass"

*An iteration without measurable success criteria cannot be validated.*

---

**Condition 5 — The rollback path exists.**

Every implementation iteration must be reversible. The previous state must be recoverable without data loss. This may mean:
- Parallel implementation alongside existing code
- Feature flags
- Database migrations with reverse scripts
- Data backups before migration

*An iteration without a rollback path is a risk, not an improvement.*

---

**Condition 6 — The invariants are preserved.**

The implementation must not violate any architectural invariant (Part VII). Violations must be:
- Impossible by design (enforced at schema or type level)
- Or detected immediately (enforced by tests or runtime checks)
- Or documented with extraordinary justification

*An iteration that violates an invariant without justification is not accepted.*

---

### 9.3 Minimum Viable Readiness for Iteration 1

The project is ready for Iteration 1 (Hypothesis Foundation) when:

1. This document (03_IMPLEMENTATION_BRIDGE.md) is reviewed and accepted
2. The Hypothesis object definition (02_SCIENTIFIC_OBJECT_MODEL.md — Object 1) is finalized
3. The traceability chain for Iteration 1 is documented
4. The existing MVP's schema, database, and pipeline are understood well enough to design Hypothesis integration
5. Success criteria for Iteration 1 are defined and measurable
6. A rollback plan exists (Hypothesis tables can be dropped without affecting events/trades)

None of these conditions require code. They require understanding, agreement, and planning.

---

## PART X: The ERA II Engineering Manifesto

### 10.1 First Principles of Engineering

**Engineering follows science.** No component is built because it is technically interesting. Every component exists because a scientific object requires it. The object model defines what exists. Engineering implements it.

**Code follows objects.** The structure of the code reflects the structure of the object model. Hypothesis has a file (or module) because it is a first-class object. Evidence has a file because it has an independent lifecycle. There is no `utils.py` that accumulates unrelated logic because each object has clear boundaries.

**Objects follow philosophy.** The object model was derived from the first-principles documents. Every object traces to a concept that was justified in philosophy. No object exists without a philosophical foundation.

**Philosophy follows evidence.** The first-principles documents are not final. When evidence contradicts a philosophical position, the philosophy yields. The documents are updated. The objects may be revised or removed.

**Evidence follows reality.** Evidence is produced by experiments. Experiments test hypotheses. Hypotheses are claims about reality. If reality contradicts the hypothesis, the hypothesis is wrong — not reality.

**Reality has the final word.** No amount of elegant philosophy, well-designed objects, or clean code can override what actually happens when the system runs. The outcome is the ultimate authority.

### 10.2 Engineering Commitments

**We build the minimum necessary to test the hypothesis.** Every feature is evaluated against the question: "Is this necessary to test the current hypothesis?" If not, it is deferred. Building more than necessary is the most common form of engineering waste.

**We preserve what works while adding what is needed.** The existing MVP works for its purpose. ERA II additions run alongside it. No existing functionality is removed until its replacement is validated.

**We measure before and after.** Every change is evaluated against a baseline. If the change does not improve criterion-relevant metrics, it is not an improvement. If it degrades them without scientific justification, it is reverted.

**We document assumptions.** Every implementation decision rests on assumptions. Assumptions are documented with the decision. When evidence contradicts an assumption, the decision is revisited.

**We keep the invariants.** The eight invariants (Part VII) are not negotiable. Any proposal that violates them must be rejected, regardless of its apparent benefits.

**We accept provisionality.** Every object, every schema, every lifecycle is provisional. It may be revised or removed when evidence demonstrates a better approach. The code should be structured to allow change, not to prevent it.

### 10.3 What Engineering Does Not Do

Engineering does not:
- Add components without scientific justification
- Optimize metrics that do not trace to criterion dimensions
- Build infrastructure before the objects it serves exist
- Create abstractions that hide the object model
- Choose frameworks that constrain the philosophy
- Prioritize speed over scientific validity
- Hide failures or inconvenient results

---

## Self-Review

### S-01: Challenge the Roadmap

**Challenge: Are eight iterations too many?**

The roadmap proposes eight sequential iterations. This is aggressive for a project that currently has zero scientific objects implemented. Each iteration depends on previous ones. A delay in Iteration 1 blocks everything.

**Response:** The dependencies are directional, not absolute. Iterations 3 (hypothesis-linked decisions) and 4 (outcome comparison) could proceed with a simplified Hypothesis (ID + title only) before the full lifecycle is implemented. The roadmap is a recommendation, not a schedule. Parallel tracks are possible.

**Challenge: Should Knowledge extraction wait until Iteration 6?**

Knowledge extraction depends on DecisionRecords (Iteration 5), which depend on all prior objects. This places knowledge extraction six iterations deep — potentially months away.

**Response:** A simplified knowledge extraction (template-based, one-knowledge-per-outcome) could be introduced at Iteration 4, when outcome comparison exists. The knowledge would be primitive (e.g., "The hypothesis was confirmed/rejected because [reason]"). The full lifecycle can wait. This would accelerate learning feedback.

### S-02: Attempt to Simplify

**Simplify: Merge Iterations 1 and 2.**

Hypothesis and Evidence are conceptually connected. A hypothesis without evidence is an opinion. Building them in separate iterations may produce a Hypothesis that cannot be evaluated.

**Verdict:** Accepted. Iterations 1 and 2 should be merged. The first implementation iteration creates Hypothesis AND Evidence together. A hypothesis must have at least one piece of evidence to be considered FORMULATED. This prevents empty hypotheses from existing.

**Simplify: Reduce DecisionRecord to a query, not a stored object.**

DecisionRecord aggregates Hypothesis, Evidence, Decision, Outcome, Reflection, Knowledge. Instead of storing it as a separate object, it could be a query that joins these objects by a shared cycle ID.

**Verdict:** Accepted for initial implementation. DecisionRecord can be a query view rather than a stored entity. This reduces storage complexity and avoids synchronization issues between the aggregate and its components. The aggregate exists conceptually but is not independently persisted.

**Simplify: Remove ResearchProposal as a required object.**

ResearchProposal ensures experiments have purpose. But requiring it for every DecisionRecord creates overhead. An "Exploratory" default proposal can cover all cycles until criterion gaps justify specific proposals.

**Verdict:** Accepted. ResearchProposal becomes optional for initial iterations. A default "General Research" proposal exists. Specific proposals are added when the system (or researcher) identifies specific gaps to investigate.

### S-03: Remove Unnecessary Phases

**Remove: Iteration 8 (ResearchProposal) as a separate iteration.**

ResearchProposal is useful but not critical for the MVP to function as a criterion laboratory. The first seven iterations produce a complete learning loop. Research proposals can be added later without disrupting existing cycles.

**Verdict:** Accepted. ResearchProposal is deferred past the initial eight iterations. The system can generate hypotheses without formal proposals. Proposals are added when the need for experiment grouping outweighs the overhead of maintaining them.

### S-04: Revised Minimal Roadmap

After simplification and removal:

| Iteration | Objective | Scientific Value |
|-----------|-----------|------------------|
| **1** | Hypothesis + Evidence Foundation | Critical |
| **2** | Hypothesis-Linked Decisions | High |
| **3** | Outcome Comparison + Error Classification | High |
| **4** | DecisionRecord (as query) + Reflection | High |
| **5** | Knowledge Extraction (simplified) | Critical |
| **6** | CriterionSnapshot Computation | Critical |
| — | ResearchProposal (deferred) | Medium |

**6 iterations instead of 8. 25% reduction.**

### S-05: Remaining Assumptions

1. **The existing MVP can be extended without breaking existing functionality.** This is true for the separation described (parallel implementation, no removal of existing components). It has been true for all prior extensions (WorldMonitorV2 was added alongside V1).

2. **The object model is stable enough to implement.** The seven objects from 02_SCIENTIFIC_OBJECT_MODEL.md have been reviewed and accepted. They will evolve, but the core relationships (hypothesis → evidence → decision → outcome → knowledge) are unlikely to change.

3. **Engineers can work within the invariants.** The eight invariants (Part VII) are clear, specific, and verifiable. They provide guidance for design decisions.

### S-06: Hidden Risks

1. **The hypothesis lifecycle may be too complex for the first iteration.** The full lifecycle has 10 states (from 14_HYPOTHESIS_LIFECYCLE_MANAGER.md) simplified to 7 in the object model. Even 7 states may be too many for the first implementation. Consider starting with 4 states: FORMULATED → ACTIVE → EVALUATED → ARCHIVED.

2. **Evidence decay may require data that does not exist.** Evidence decay depends on domain velocity. For trading, evidence may decay in days. But the project has no data on optimal decay rates. The first implementation should use a simple time-based decay with a configurable half-life, then adjust based on empirical data.

3. **Error classification may be too subjective for automation.** Error types (wrong hypothesis, wrong timing, poor execution) require judgment. In early iterations, classification will need human review. The system should not automate error classification until consistency is demonstrated.

### S-07: What Should Be Challenged Before Implementation

1. **Should the first Hypothesis be created by the system or by a human?** The roadmap assumes hypotheses can be created. But who creates them? If the system generates them, they may be low quality. If humans create them, the system is not autonomous. Answer: Start with human-created hypotheses to establish quality. Add system-generated hypotheses when the formation mechanism is validated.

2. **Should Evidence always require a Hypothesis, or can evidence exist independently?** The object model says evidence is always relative to a hypothesis. But in practice, the system collects observations that are not yet linked to any hypothesis. Answer: Observations can be collected without a hypothesis. They become Evidence only when linked to one.

3. **Should the existing pipeline continue running during ERA II implementation?** Running two systems (operational MVP + scientific layer) creates overhead. But stopping the MVP halts data collection. Answer: The MVP continues running. ERA II additions run in parallel. The MVP provides the experimental environment; the scientific layer records and analyzes the experiments.

---

## Final Declaration

O.M.A.-C.O.R.E. will not evolve by adding more code.

It will evolve by increasing the correspondence between reality, evidence, architecture, and implementation.

Every line of code must trace to a scientific object. Every scientific object must trace to a philosophical concept. Every philosophical concept must be justified by evidence. Every claim of evidence must connect back to reality.

When a trade loses money but disproves a hypothesis, the system has learned.

When a trade makes money but teaches nothing, the system has not progressed.

The bridge between philosophy and implementation is not built with code. It is built with understanding — precise understanding of what each object is, why it exists, what it produces, and how it connects to everything else.

Code comes last. Understanding comes first.

Everything remains provisional.

Everything remains falsifiable.

Evidence always has the final word.

---

*End of 03_IMPLEMENTATION_BRIDGE.md — Version 1.0 — June 2026*
