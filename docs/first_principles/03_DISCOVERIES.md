# Discoveries

*A structured log of conceptual discoveries made during the evolution of O.M.A.-C.O.R.E.*

---

## Discovery 1: Criterion

**Context:** The project began as a trading system. It was evaluated by PnL, win rate, and Sharpe ratio. After months of development and hundreds of trades, it became clear that these metrics measured outcomes but not improvement. A system could be profitable without learning, or unprofitable while learning.

**Problem solved:** The project needed a north star that was not tied to immediate performance. Criterion — the accumulated ability to judge what matters — provided a metric that could improve even during drawdowns, as long as the system learned from its errors.

**Reasoning:** If the only goal is profit, the system will optimize for short-term gain at the expense of long-term learning. If the goal is criterion, every outcome — win or loss — becomes a learning opportunity. The system that optimizes for criterion will eventually outperform the system that optimizes for profit, because criterion compounds while profits fluctuate.

**Potential validation:** A system with high criterion should show:
- Improving decision quality over time (measured by outcome-to-hypothesis alignment)
- Decreasing error repetition (the same mistake is not made twice)
- Increasing calibration accuracy (confidence aligns with actual accuracy)
- Stable performance across different market regimes

**Open questions:**
- Can criterion be measured directly, or only inferred from behavior?
- Does criterion transfer between domains (trading to creation to entrepreneurship)?
- How long does it take for criterion to develop to a practically useful level?

**Future implications:** Criterion may become the central metric by which the system is evaluated, replacing or supplementing PnL, Sharpe ratio, and win rate.

---

## Discovery 2: Consequence Intelligence

**Context:** The system detected events, analyzed them, and generated trading signals. But signals are downstream of something more fundamental: the system's ability to recognize what consequences may emerge from an event.

**Problem solved:** Separating consequence detection from opportunity generation allowed each to be optimized independently. A consequence may be detected but not acted upon (if it does not meet the opportunity threshold). An opportunity should always trace back to a consequence.

**Reasoning:** Events are inputs. Consequences are predictions about future states. Opportunities are actions justified by those predictions. By separating these layers, the system can improve its consequence detection without changing its opportunity generation, and vice versa.

**Potential validation:** A system with consequence intelligence should detect consequences before they become obvious to the majority, with accuracy that improves over time.

**Open questions:**
- How many events are needed to detect a consequence reliably?
- What is the false positive rate of early consequence detection?
- Can consequences be classified by type (economic, social, political, technological)?

**Future implications:** Consequence detection may become the primary function of the perception layer, with opportunity generation as a downstream consumer.

---

## Discovery 3: Hypothesis Tracking

**Context:** The system recorded trades and their outcomes, but could not answer *why* a trade was right or wrong. The hypothesis that led to the trade was not preserved. Without the hypothesis, the outcome was an isolated data point.

**Problem solved:** Hypothesis tracking connects outcomes to the reasoning that produced them. When a trade wins, the system can ask: was the hypothesis correct, or was it luck? When a trade loses, the system can ask: was the hypothesis wrong, or was the execution poor?

**Reasoning:** An outcome without a hypothesis is noise. An outcome with a hypothesis is evidence. Over many outcomes, hypotheses can be evaluated, refined, or discarded. The unit of learning is not the trade — it is the hypothesis.

**Potential validation:** The system should show improving hypothesis quality over time: hypotheses become more precise, invalidation conditions become more accurate, confidence calibration improves.

**Open questions:**
- What is the ideal level of hypothesis granularity?
- Should hypotheses compete, or coexist?
- How long should a hypothesis be tracked after the trade closes?

**Future implications:** Hypothesis tracking may become the bridge between execution and learning — the component that turns raw outcomes into accumulated criterion.

---

## Discovery 4: Failure Intelligence

**Context:** Every system fails. The question is whether the system learns from failure. In early versions of OSIRIS, a failed trade produced only a PnL number. There was no classification of the failure type, no decomposition of its causes.

**Problem solved:** Classifying failures by type — wrong event interpretation, wrong correlation, wrong consequence, correct consequence but wrong timing, correct hypothesis but poor execution — allows the system to learn different lessons from different failure modes.

**Reasoning:** Not all failures are equal. A failure caused by an external shock (black swan) teaches a different lesson than a failure caused by poor execution. A failure caused by a wrong hypothesis teaches a different lesson than a failure caused by correct timing but poor entry. By classifying failures, the system can learn from each type independently.

**Potential validation:** The system should show decreasing frequency of each failure type over time, as lessons are learned and applied.

**Open questions:**
- How many failure categories are sufficient?
- Can failure types be detected automatically?
- Which failures are acceptable (external shocks) vs unacceptable (repeated errors)?

**Future implications:** Failure intelligence may evolve into a self-diagnosis system that identifies the system's weaknesses and recommends corrective actions.

---

## Discovery 5: Capital Allocation as an Intelligence Problem

**Context:** Extended Demo telemetry revealed a persistent pattern: signals continued to be generated, but execution was blocked by capacity limits. The system had reached a policy-driven bottleneck.

**Problem solved:** Recognizing that capital allocation is not an execution detail but a core intelligence problem. The question "should I replace my weakest position with this new opportunity" is fundamentally different from "can I execute this signal."

**Reasoning:** A system that generates opportunities but cannot compare them is missing the most important step. The value of the system is not in generating the largest number of opportunities, but in consistently allocating scarce capital to the most deserving ones.

**Potential validation:** A system with intelligent capital allocation should show higher portfolio quality (measured by average conviction of open positions) and higher capital efficiency (measured by return per unit of risk).

**Open questions:**
- What is the optimal number of simultaneous positions?
- Should position size vary with conviction, or be fixed?
- How should replacement costs be estimated?

**Future implications:** Capital allocation may become a separate engine that sits between opportunity generation and execution.

---

## Discovery 6: Opportunity Capture Rate

**Context:** The system could measure its win rate, but could not measure what it was missing. Was the system capturing 10% of valid opportunities, or 90%? Without knowing, improvement was blind.

**Problem solved:** Opportunity Capture Rate — the ratio of profitable opportunities detected to profitable opportunities that existed in the observed market window — provides an upper bound on potential improvement. If the capture rate is 20%, there is room to improve detection. If it is 80%, the bottleneck is elsewhere.

**Reasoning:** A system can only improve what it can measure. Measuring only what the system caught (trades) without measuring what it missed (opportunities) creates an incomplete picture.

**Potential validation:** This metric is extremely difficult to measure in practice (it requires knowing what opportunities existed beyond those detected). But even an approximate version would inform development priorities.

**Open questions:**
- How can this metric be approximated without perfect knowledge?
- What is a good capture rate? 50%? 80%?
- Does capture rate vary by market condition?

**Future implications:** Opportunity Capture Rate may become a key metric for evaluating perception quality separately from execution quality.

---

## Discovery 7: Cluster Intelligence

**Context:** The system detected individual events and individual correlations. But the most reliable signals come not from single events, but from clusters of related events pointing toward the same consequence.

**Problem solved:** Cluster intelligence connects events that are related but independently weak into a stronger signal. Multiple weak signals converging on the same consequence produce higher confidence than any single signal.

**Reasoning:** A single rate cut is weak evidence for a gold rally. A rate cut plus weak dollar plus gold ETF inflows plus mining sector strength is stronger evidence — not because any single signal is better, but because multiple independent signals converge on the same consequence.

**Potential validation:** A cluster-based system should show higher accuracy for consequences supported by multiple independent signals, compared to consequences supported by single signals.

**Open questions:**
- How are clusters formed automatically?
- What is the minimum number of events needed for a meaningful cluster?
- How should contradictory evidence within a cluster be weighted?

**Future implications:** Cluster intelligence may become a primary filtering layer between raw events and consequence detection.

---

## Discovery 8: Operational Criterion

**Context:** The project's mission shifted from "predict markets" to "develop criterion." But criterion that never leads to action is academic. The system needs operational criterion — judgment that informs real decisions.

**Problem solved:** Operational criterion bridges the gap between accumulated knowledge and moment-to-moment decisions. It is the application of past learning to present choices.

**Reasoning:** Criterion without operation is philosophy. Operation without criterion is reactivity. The system needs both: the accumulated depth of criterion and the practical application of operational decisions.

**Potential validation:** The system should show a measurable relationship between criterion maturity and decision quality. Decisions made with more accumulated experience should outperform decisions made with less.

**Open questions:**
- At what point does operational criterion become distinguishable from random?
- How much experience is needed to develop basic operational criterion?

**Future implications:** Operational criterion may become the central measure of system maturity.

---

## Discovery 9: Decision Quality

**Context:** The system could measure outcome quality (PnL) but not decision quality. A profitable trade could be the result of a bad decision that got lucky. An unprofitable trade could be the result of a good decision that got unlucky.

**Problem solved:** Separating decision quality from outcome quality allows the system to evaluate itself on what it can control (decisions) rather than what it cannot (outcomes).

**Reasoning:** In complex systems, outcomes are determined by a combination of decision quality and luck. A system that evaluates itself only by outcomes will reinforce lucky decisions and punish unlucky ones, leading to superstitious behavior. A system that evaluates itself by decision quality — given the information available at the time — will improve its actual decision-making ability regardless of short-term outcomes.

**Potential validation:** A system that optimizes for decision quality should show better risk-adjusted returns over long time horizons than a system that optimizes for outcome quality.

**Open questions:**
- How can decision quality be measured independently of outcomes?
- What is the right time horizon for evaluating decision quality?

**Future implications:** Decision quality may become the primary feedback signal for learning, with outcomes used only for calibration.
