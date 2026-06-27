# Scarce Resources Model

## O.M.A.-C.O.R.E. Decision Intelligence — Component 3

*Version 1.0 — June 2026*

---

## 1. Purpose

The Scarce Resources Model defines the complete ontology of scarce resources that O.M.A.-C.O.R.E. consumes, generates, and protects. This document is the bridge between the abstract concept of "Criterion" and the concrete reality of resource management. It answers three questions:

1. **What does the system consume every time it acts?**
2. **What does the system generate when it learns effectively?**
3. **Why is maximizing scarce resource generation the correct objective function?**

---

## 2. Why Money Is Not the Primary Objective

Money (capital) is the most visible scarce resource but the least informative one for decision intelligence. Here is why the system does not optimize for money:

| Reason | Explanation |
|---|---|
| **Money is a proxy, not a purpose** | Money represents past resource generation. Optimizing for money optimizes for a lagging indicator. |
| **Money is reversible** | Lost money can be re-generated if other resources remain intact. Lost trust, reputation, or knowledge may be irrecoverable. |
| **Money follows criterion, not vice versa** | If the system develops strong criterion, money is a natural consequence. Optimizing for money directly creates perverse incentives (short-term extraction over long-term learning). |
| **Money is only one resource axis** | A system with unlimited money but zero attention, depleted trust, and degraded knowledge cannot function. Money alone is insufficient for execution. |
| **Money maximization is a solved problem for known environments** | The system's purpose is to operate in unknown, changing environments where static optimization fails. |

**The real purpose of O.M.A.-C.O.R.E. is maximizing scarce resource generation across all dimensions, weighted by their criticality to the system's continued operation and growth.**

---

## 3. Resource Ontology

Each resource entry follows a consistent template:

- **Definition**: What the resource is.
- **Why Scarce**: Why it is limited and cannot be trivially expanded.
- **How Generated**: Actions or conditions that increase the resource.
- **How Consumed**: Actions or conditions that decrease the resource.
- **How Protected**: Mechanisms that prevent depletion.
- **How Converted**: The resource can be exchanged for other resources.
- **How Measured**: Units and measurement approach.
- **Criterion Conversion Efficiency**: How improved criterion reduces the resource cost per decision or increases generation per unit input.
- **Destruction Pattern**: How poor decisions destroy this resource.

---

### 3.1 Capital (C)

| Property | Description |
|---|---|
| **Definition** | Liquid financial assets available for deployment. The operational fuel. |
| **Why Scarce** | Finite by definition for a non-printing entity. Composable but bounded by external constraints (account size, leverage limits, regulatory caps). |
| **How Generated** | Successful position exits, external deposits, interest/returns on deployed capital. |
| **How Consumed** | Position entries, fees, slippage, losses, operational costs, data subscriptions. |
| **How Protected** | Position sizing bounds, stop losses, kill switch, capital guard, diversification requirements. |
| **How Converted** | ↔ Attention (paid research/data), ↔ Compute (infrastructure), → Reputation (capital growth attracts trust), → Knowledge (capital enabled experiments). |
| **How Measured** | Currency units (USD). Metrics: total capital, free capital, deployed capital, drawdown from peak. |
| **Criterion Conversion** | Better criterion increases win rate and average risk-adjusted return per unit of capital deployed. Converts capital into knowledge more efficiently. |
| **Destruction Pattern** | Reckless deployment without hypothesis testing. Overtrading. Ignoring drawdown limits. Chasing losses. |

---

### 3.2 Time (T)

| Property | Description |
|---|---|
| **Definition** | The finite temporal budget available for observation, reasoning, decision, and execution. |
| **Why Scarce** | Absolute constraint. Every decision cycle consumes time that cannot be recovered. Markets move on time scales the system cannot control. |
| **How Generated** | Cannot be generated. Only conserved by not spending on low-value activities. |
| **How Consumed** | Every observation, analysis, deliberation, and execution step. Decisions that result in WAIT or NEED_MORE_EVIDENCE also consume time. |
| **How Protected** | Time budgets per decision cycle. Maximum deliberation time. Parallel processing where possible. |
| **How Converted** | → Knowledge (time spent analyzing produces knowledge), → Capital (well-timed execution), ↔ Attention (faster decisions require more attention per unit time). |
| **How Measured** | Wall-clock time (milliseconds, seconds, minutes, hours, cycles). |
| **Criterion Conversion** | Criterion reduces time spent on routine decisions (pattern recognition replaces deliberation). Frees time for novel situations. |
| **Destruction Pattern** | Analysis paralysis. Excessive re-evaluation. Unbounded reasoning loops. Premature execution requiring costly corrections. |

---

### 3.3 Attention (A)

| Property | Description |
|---|---|
| **Definition** | The system's finite capacity to process information and make distinctions. |
| **Why Scarce** | Computational and architectural limits. The system can only evaluate a bounded number of hypotheses, evidence items, and decisions per cycle. |
| **How Generated** | Completing decisions (frees attention). Expanding compute resources. Batching similar decisions. |
| **How Consumed** | Opening new hypotheses. Evaluating evidence. Deliberating on decisions. Monitoring open positions. Processing new events. |
| **How Protected** | Maximum concurrent hypothesis limits. Attention budgeting per decision class. Prioritization queues. |
| **How Converted** | → Knowledge (attention spent on analysis), → Capital (attention on high-value opportunities), → Criterion (attention on learning from outcomes). |
| **How Measured** | Concurrent open hypotheses. Active evidence evaluations. Pending decisions. Cycle utilization percentage. |
| **Criterion Conversion** | Criterion focuses attention on high-signal information and reduces attention wasted on noise. Higher criterion means more decisions per unit attention. |
| **Destruction Pattern** | Opening too many hypotheses simultaneously. Over-analyzing low-value decisions. Failing to close evaluated hypotheses. Attention fragmentation across irrelevant domains. |

---

### 3.4 Energy (E)

| Property | Description |
|---|---|
| **Definition** | The system's capacity to sustain operation and maintain decision quality under load. |
| **Why Scarce** | All physical and virtual systems have operational limits. Heat, power, and component degradation constrain sustained throughput. |
| **How Generated** | Rest periods. Hardware upgrades. Load balancing. Efficient algorithms. |
| **How Consumed** | Sustained high-frequency operation. Complex computations. Large-scale data processing. |
| **How Protected** | Rate limiting. Graceful degradation under load. Scheduled maintenance windows. Computational budgets. |
| **How Converted** | → Attention (energy enables sustained focus), → Time (more energy = more decisions per cycle). |
| **How Measured** | CPU utilization, memory pressure, API call rate, power consumption, system uptime. |
| **Criterion Conversion** | Criterion reduces wasted computation (no unnecessary re-analysis). Efficient pattern matching replaces brute-force search. |
| **Destruction Pattern** | Running at maximum capacity continuously. Ignoring degradation signals. Not budgeting for maintenance. |

---

### 3.5 Trust (Tr)

| Property | Description |
|---|---|
| **Definition** | The confidence that the system's decisions are well-founded, consistent, and aligned with stated objectives. |
| **Why Scarce** | Trust is built slowly through demonstrated reliability and destroyed instantly by a single catastrophic failure. It is asymmetric — losses damage trust more than gains build it. |
| **How Generated** | Consistent performance. Transparent decision logging. Honest uncertainty communication. Following stated policies. |
| **How Consumed** | Unexplained failures. Opaque decisions. Violating policy. High-severity errors. Frequent human override requirements. |
| **How Protected** | Full decision audit trail. Explanation generation. Policy adherence enforcement. Emergency stop prevents catastrophic trust loss. |
| **How Converted** | ↔ Reputation (trust is internal, reputation is external), → Autonomy (more trust enables more autonomy). |
| **How Measured** | Human override rate. Unexplained decision ratio. Policy compliance percentage. Mean time between trust-eroding events. |
| **Criterion Conversion** | Criterion improves decision quality and consistency, which directly builds trust. Transparent criterion evolution demonstrates principled improvement. |
| **Destruction Pattern** | One black swan loss without explanation. Silent failures. Unexplained policy changes. Misaligned incentives (system optimizing for something other than what was stated). |

---

### 3.6 Reputation (Re)

| Property | Description |
|---|---|
| **Definition** | External stakeholders' perception of the system's competence, reliability, and value. |
| **Why Scarce** | External reputation depends on factors partially outside the system's control (market conditions, competitor actions, public sentiment). Slower to build than trust. |
| **How Generated** | Consistent external results. Transparent communication. Acknowledging mistakes. Demonstrating learning over time. |
| **How Consumed** | Public failures. Unexplained losses. Inconsistent behavior. Perceived unpredictability. |
| **How Protected** | External communication policies. Reputation buffer (maintain reserves of goodwill). Proactive transparency. |
| **How Converted** | → Trust (external reputation reinforces internal trust), → Capital (attracts investment), → Opportunity (preferential access). |
| **How Measured** | Qualitative (stakeholder surveys, external feedback). Proxy metrics: capital inflow rate, partnership requests, media coverage sentiment. |
| **Criterion Conversion** | Criterion creates explainable, defensible decisions that can be communicated externally. A system that can explain *why* it lost money preserves more reputation than one that cannot. |
| **Destruction Pattern** | Catastrophic unmanaged loss. Perceived recklessness. Inability to explain decisions. Repeated same-class failures without evidence of learning. |

---

### 3.7 Knowledge (K)

| Property | Description |
|---|---|
| **Definition** | Validated, structured information that improves future decision quality. |
| **Why Scarce** | Knowledge requires experience (time + attention + capital) to generate. It degrades without replication. False knowledge actively harms future decisions. |
| **How Generated** | Outcome comparison → knowledge extraction → validation → replication. Each step consumes other resources and risks producing no useful knowledge. |
| **How Consumed** | Knowledge is not consumed by use (non-rivalrous). It is consumed by decay (time without replication). |
| **How Protected** | Decay functions. Replication requirements. Knowledge lifecycle state machine. Provenance tracking prevents untrusted knowledge from being used. |
| **How Converted** | → Criterion (knowledge accumulation produces criterion), → Capital (better decisions produce better returns), → Trust (demonstrated learning builds confidence). |
| **How Measured** | Count of validated knowledge items. Knowledge confidence distribution. Domain coverage. Replication depth. Average knowledge half-life. |
| **Criterion Conversion** | Criterion is meta-knowledge — knowledge about which knowledge to trust. Higher criterion means more efficient knowledge generation (less time/capital per useful knowledge unit). |
| **Destruction Pattern** | Using untested knowledge as if validated. Ignoring decay. Not replicating. Confusing correlation with causation. Confirmation bias in evidence selection. |

---

### 3.8 Liquidity (L)

| Property | Description |
|---|---|
| **Definition** | The ability to enter and exit positions at predictable prices. |
| **Why Scarce** | Market depth is finite and varies by instrument, time, and market conditions. Large positions face slippage. Illiquid periods can trap capital. |
| **How Generated** | Trading liquid instruments. Favorable market conditions. Small position sizes relative to market depth. |
| **How Consumed** | Every trade consumes liquidity. Large trades consume more. Panic exits consume disproportionate liquidity. |
| **How Protected** | Position sizing relative to volume. Slippage estimation. Liquidity regime detection. Avoiding low-liquidity windows. |
| **How Converted** | ↔ Capital (liquidity enables capital deployment, capital attracts liquidity providers). |
| **How Measured** | Bid-ask spread. Order book depth. Average daily volume. Slippage history. |
| **Criterion Conversion** | Criterion identifies optimal liquidity windows and appropriate position sizes for current liquidity conditions. Avoids forced exits in illiquid conditions. |
| **Destruction Pattern** | Overtrading in illiquid instruments. Ignoring slippage trends. Emergency exits that compound liquidity problems. |

---

### 3.9 Execution Bandwidth (X)

| Property | Description |
|---|---|
| **Definition** | The capacity to execute decisions through operational channels per unit time. |
| **Why Scarce** | Exchange rate limits, API rate limits, network latency, and order processing capacity bound execution throughput. |
| **How Generated** | Infrastructure upgrades. Multiple execution venues. Reduced order frequency. |
| **How Consumed** | Every order submission consumes bandwidth. Cancel-replace cycles consume more. Failed executions consume bandwidth without benefit. |
| **How Protected** | Rate limit awareness. Order batching. Execution priority queues. Circuit breakers for excessive order activity. |
| **How Converted** | ↔ Capital (bandwidth enables capital deployment), → Time (higher bandwidth = faster execution). |
| **How Measured** | Orders per second/minute/hour. API call count. Execution queue depth. |
| **Criterion Conversion** | Criterion reduces unnecessary orders (fewer failed entries, fewer panic exits, fewer cancel-replace cycles). Each execution carries more intention. |
| **Destruction Pattern** | HFT-style churn without hypothesis. Over-optimizing entries (multiple cancel-replace). Panic exits flooding execution channels. |

---

### 3.10 Compute (Cp)

| Property | Description |
|---|---|
| **Definition** | Available processing capacity for analysis, reasoning, and decision computation. |
| **Why Scarce** | Bounded by hardware, cloud budget, and architectural parallelism limits. Some computations (e.g., full historical replay) are expensive. |
| **How Generated** | Hardware upgrades. Cloud scaling. Algorithmic optimization. Reduced unnecessary computation. |
| **How Consumed** | Real-time analysis. Evidence evaluation. Hypothesis generation. Confidence engine computation. Replay sessions. |
| **How Protected** | Computational budgets per component. Priority scheduling. Degradation modes for expensive operations. |
| **How Converted** | → Knowledge (compute enables analysis), → Confidence (compute enables calibration), ↔ Attention (compute enables broader attention). |
| **How Measured** | CPU seconds. Memory allocation. API call volume. Replay session cost. |
| **Criterion Conversion** | Criterion replaces compute-expensive brute-force search with pattern matching and directed analysis. More decisions per unit compute. |
| **Destruction Pattern** | Running full replay on every cycle. Unbounded evidence search. Redundant computation across components. |

---

### 3.11 Memory (M)

| Property | Description |
|---|---|
| **Definition** | Storage and retrieval capacity for historical data, decisions, and learned patterns. |
| **Why Scarce** | Storage is finite. More importantly, retrieval quality degrades with volume (the search space grows). Not all memories can be equally accessible. |
| **How Generated** | Pruning low-value memories. Efficient indexing. Summarization. |
| **How Consumed** | Every observation, decision, and outcome committed to memory consumes storage. Poorly structured memories consume retrieval performance. |
| **How Protected** | Retention policies. Memory pruning (archive old, compress large). Summary generation for long-running memories. |
| **How Converted** | → Knowledge (structured memory becomes knowledge), → Criterion (long-term memory enables pattern recognition across time). |
| **How Measured** | Storage used. Retrieval latency. Memory density (useful signals per MB). Pruning rate. |
| **Criterion Conversion** | Criterion identifies which memories to retain and which to prune. Reduces noise in the memory store. Improves signal-to-noise ratio per byte. |
| **Destruction Pattern** | Retaining everything (no pruning). Losing critical memories due to poor indexing. Storing contradictory memories without resolution. |

---

### 3.12 Opportunity (O)

| Property | Description |
|---|---|
| **Definition** | The set of favorable action possibilities available at a given time. |
| **Why Scarce** | Opportunities are time-bounded and mutually exclusive. Acting on one opportunity forecloses others by consuming attention, capital, and time. |
| **How Generated** | Generating opportunities requires attention, capital, and knowledge. Each opportunity is a hypothesis that *this action will generate net positive resources*. |
| **How Consumed** | Every decision to act consumes the opportunity. Every decision not to act may cause the opportunity to expire. |
| **How Protected** | Opportunity evaluation before commitment. Opportunity ranking by expected resource yield. Maintaining slack capacity to capture unexpected opportunities. |
| **How Converted** | → Capital (executed opportunities produce returns), → Knowledge (even failed opportunities produce learning). |
| **How Measured** | Available opportunity count per decision class. Opportunity expiration rate. Opportunity conversion rate (fraction that become actions). |
| **Criterion Conversion** | Criterion improves opportunity selection — the ability to identify which opportunities are worth pursuing and which are distractions. A high-criterion system generates more value per opportunity. |
| **Destruction Pattern** | Pursuing too many opportunities simultaneously (attention collapse). Letting high-value opportunities expire while pursuing low-value ones. Not recognizing opportunities due to rigid heuristics. |

---

### 3.13 Human Supervision (H)

| Property | Description |
|---|---|
| **Definition** | The finite capacity of human operators to review, override, and guide system decisions. |
| **Why Scarce** | One-person maintainability constraint. One human cannot supervise unlimited decisions. Supervision requires attention, time, and domain expertise that are inherently limited. |
| **How Generated** | By not wasting human attention on routine decisions. By generating clear, concise explanations. By batching exceptions. |
| **How Consumed** | Every escalation to L2+ consumes human supervision. Every human override requires context review. Every policy question requires human judgment. |
| **How Protected** | Escalation budgets. Clear distinction between routine and exceptional. Autonomous handling of all Tier 1 decisions. |
| **How Converted** | → Trust (appropriate supervision builds trust), → Autonomy (good supervision enables autonomy expansion). |
| **How Measured** | Escalations per cycle. Human response time. Override rate. Decisions per human review hour. |
| **Criterion Conversion** | Criterion reduces the frequency of novel situations requiring human judgment. The system learns to handle edge cases that previously required escalation. |
| **Destruction Pattern** | Escalating everything (overwhelms the human). Escalating nothing (risks unsupervised catastrophic failure). Poor explanations that force the human to re-derive the decision from scratch. |

---

### 3.14 Data Quality (D)

| Property | Description |
|---|---|
| **Definition** | The accuracy, completeness, timeliness, and relevance of information entering the system. |
| **Why Scarce** | All real-world data sources are noisy, delayed, or incomplete. Improving quality requires spending other resources (capital for better feeds, attention for validation). |
| **How Generated** | Source diversification. Cross-validation across channels. Anomaly detection and filtering. Feedback loops that tag low-quality data. |
| **How Consumed** | Every observation consumes data quality budget (even low-quality data must be processed to determine it is low quality). |
| **How Protected** | Quality scoring on every data source. Minimum quality thresholds for evidence generation. Degradation alerts when sources decline. |
| **How Converted** | → Knowledge (high-quality data enables reliable knowledge), → Confidence (better data reduces uncertainty). |
| **How Measured** | Source reliability scores. Data freshness metrics. Anomaly rate. Completeness percentage per source. |
| **Criterion Conversion** | Criterion enables the system to identify which data dimensions matter and which are noise. Reduces the quality threshold needed for effective decisions by focusing on high-signal dimensions. |
| **Destruction Pattern** | Trusting low-quality data sources without validation. Ignoring degradation signals. Using stale data for time-sensitive decisions. |

---

### 3.15 Information Advantage (I)

| Property | Description |
|---|---|
| **Definition** | The edge gained by having access to information that competitors do not have, or by interpreting shared information more accurately. |
| **Why Scarce** | Information advantage is zero-sum in competitive markets. Once an insight is widely known, its advantage is eliminated. Advantage decays as others catch up. |
| **How Generated** | Unique data sources. Proprietary analysis methods. Faster interpretation. Criterion enables recognition of patterns others miss. |
| **How Consumed** | Acting on an advantage consumes it (the market moves toward equilibrium). Publishing or revealing an advantage accelerates its consumption. |
| **How Protected** | Selective execution. Not revealing analysis methods. Avoiding patterns that others can front-run. |
| **How Converted** | → Capital (information advantage directly produces profitable trades), → Reputation (demonstrated edge attracts partners). |
| **How Measured** | Advantage half-life. Uniqueness of information sources. Time between discovery and market saturation. |
| **Criterion Conversion** | Criterion is the most durable form of information advantage. It is the ability to generate new advantages faster than existing ones decay. A high-criterion system does not depend on any single information edge. |
| **Destruction Pattern** | Becoming dependent on a single information source. Not recognizing when an advantage has decayed. Revealing edges through predictable behavior. |

---

## 4. Resource Conversion Map

The following diagram shows which resources can be converted into which:

```
        Capital ←→ Time ←→ Compute
           ↑        ↑        ↑
           │        │        │
    Attention ←→ Knowledge → Criterion
           ↑        ↑
           │        │
    Data Quality  Energy
           │
           ↓
    Information Advantage → Reputation → Trust
                                ↑
                           Opportunity
                                ↑
                           Human Supervision
                                ↓
                            Autonomy
```

Solid arrows represent direct, well-defined conversion paths. Dashed relationships exist but with significant loss. The central role of **Knowledge** and **Criterion** is visible — they are the most convertible resources in the ontology, because they improve the efficiency of all other conversions.

---

## 5. Resource Criticality Matrix

| Resource | Depletion Speed | Regeneration Speed | Irrecoverability | System Criticality |
|---|---|---|---|---|
| Capital | Fast | Slow | Low (can regenerate) | Operational |
| Time | Instant | None | Absolute | Universal |
| Attention | Fast | Medium | Medium | Operational |
| Energy | Medium | Fast | Low | Operational |
| Trust | Slow building, instant loss | Very slow | High | Strategic |
| Reputation | Slow building, instant loss | Slow | Medium-High | Strategic |
| Knowledge | Medium (decay) | Slow | Medium | Core mission |
| Liquidity | Fast (in crisis) | Medium | Medium | Tactical |
| Execution BW | Fast | Fast | Low | Tactical |
| Compute | Medium | Fast | Low | Operational |
| Memory | Slow | Slow | Medium | Operational |
| Opportunity | Instant (expires) | Variable | High | Tactical |
| Human Supervision | Fast | Very slow | High | Strategic |
| Data Quality | Medium | Medium | Medium | Operational |
| Information Adv. | Fast | Very slow | High | Strategic |

**Key insight**: The fast-depleting, slow-to-regenerate resources (Trust, Reputation, Human Supervision, Information Advantage) must be the primary concern of the Decision Intelligence Layer. Capital efficiency is secondary to preserving these strategic resources.

---

## 6. Resource-Aware Decision Weighting

Every decision should be evaluated not only on expected capital return but on its impact across all scarce resources:

```
Decision Value = Σ(w_r × ΔR_r × C_r)
```

Where:
- `w_r` = policy weight for resource `r` (sums to 1.0)
- `ΔR_r` = expected change in resource `r` (positive = generation, negative = consumption)
- `C_r` = conversion efficiency factor from Criterion maturity in this dimension

The weights `w_r` are not static — they shift based on current resource depletion levels:

- If Trust is critically low, `w_Trust` dominates. The system prioritizes trust-preserving decisions even at capital cost.
- If Knowledge is abundant in a domain but Capital is depleted, `w_Capital` rises. The system prioritizes capital generation.
- If Human Supervision is near capacity, `w_HumanSupervision` rises. The system avoids decisions that would require escalation.

This dynamic weighting is what makes the system intelligent about resource allocation, rather than blindly optimizing a single metric.

---

## 7. Open Design Questions

1. Should resource weights be fixed policy parameters or learned through replay? **Current position**: Fixed policy parameters that can be updated through criterion delta proposals. Resource management is too fundamental to leave to emergent learning without human review.

2. How should resource depletion emergencies be handled when multiple critical resources are simultaneously depleted? **Current position**: Emergency stop protocol — halt all non-essential resource consumption, focus on regeneration, escalate to human.

3. Should the system maintain resource reserves (analogous to capital reserves) for non-financial resources? **Current position**: Yes — attention reserve, trust buffer, knowledge redundancy. The concept of "slack" applies to all scarce resources, not just capital.

4. Is the resource ontology complete? **Current position**: It is complete enough for Stage 9 design. New resources should be added when a proposed addition changes a decision outcome. If adding a resource never changes any decision, it is not a real resource.
