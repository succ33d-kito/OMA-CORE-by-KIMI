# Assumptions

*Every major assumption behind O.M.A.-C.O.R.E., documented explicitly so they can be examined, tested, and if necessary, abandoned.*

---

## How to Read This Document

Each assumption includes:

| Field | Purpose |
|-------|---------|
| **ID** | Unique identifier for reference |
| **Statement** | What we assume to be true |
| **Why we believe it** | The reasoning behind the assumption |
| **Supporting evidence** | What currently supports it |
| **Contradicting evidence** | What challenges it |
| **Confidence** | How sure we are (Low / Medium / High) |
| **Impact if false** | How damaging falsification would be |
| **Falsification method** | How we would know it is wrong |
| **Status** | Whether this assumption has been tested |

---

## Foundational Assumptions

### A-001: The World Produces Detectable Consequences

**Statement:** The world generates events that, when analyzed together, reveal detectable consequences — possible future states that can be recognized before they fully materialize.

**Why we believe it:** Financial markets, social systems, and biological systems all show evidence of emergent patterns that precede observable changes. Leading indicators, predictive models, and successful forecasting across many domains suggest consequences are detectable in principle.

**Supporting evidence:** The existence of reliable leading indicators in economics (yield curve inversions preceding recessions, for example). Successful prediction markets. The entire field of signal processing.

**Contradicting evidence:** Many predicted consequences never materialize. False positive rates in early detection systems are often high. Some systems may be fundamentally unpredictable (chaotic systems, human collective behavior at certain scales).

**Confidence:** Medium

**Impact if false:** **Critical.** The entire framework collapses. If consequences cannot be detected, the system degenerates into random action or noise trading.

**Falsification method:** A systematic demonstration that consequence detection accuracy does not exceed chance levels across multiple domains, after sufficient training time.

**Status:** Untested. This is the foundational hypothesis the project exists to validate.

---

### A-002: Criterion Compounds Through Experience

**Statement:** The system's ability to judge what matters improves over time as it accumulates structured experience from hypotheses, decisions, outcomes, and learning.

**Why we believe it:** Human expertise develops through deliberate practice. Systems that track and learn from their errors improve faster than those that do not. Learning curves are a well-documented phenomenon.

**Supporting evidence:** The entire field of expertise research (Ericsson, Chase & Simon). Learning curve theory. The success of feedback-driven improvement in many domains.

**Contradicting evidence:** Some systems plateau. Expertise can decay without practice. Memory can degrade. Bad habits can reinforce themselves — experience without structured learning may not produce improvement.

**Confidence:** Medium

**Impact if false:** **High.** The long-term justification for the project depends on criterion compounding. If it does not, the system's value is bounded by its initial design.

**Falsification method:** Measure criterion-relevant metrics over multiple years and show they do not improve, or that improvement plateaus below useful levels.

**Status:** Untested. Will require years of data to evaluate.

---

### A-003: Memory Quality Matters More Than Memory Quantity

**Statement:** The structure and quality of stored experience — hypotheses linked to outcomes, evidence tracked, errors classified — matters more than the raw volume of data stored.

**Why we believe it:** Systems with structured memory (linking causes to effects) learn faster than those with unstructured data. Data without structure is noise. A few well-structured experiences are more valuable than millions of unstructured data points.

**Supporting evidence:** Scientific research depends on structured experimentation, not raw data accumulation. The most successful learning systems (scientific method, deliberate practice) are structured, not volumetric.

**Contradicting evidence:** Large language models and deep learning systems achieve remarkable results through scale alone, suggesting that quantity can substitute for structure at sufficient scale. However, these systems also require enormous amounts of data and compute.

**Confidence:** Medium-High

**Impact if false:** **Medium.** If quantity matters more than quality, the project would need to prioritize data accumulation over hypothesis structure.

**Falsification method:** Compare a structured-memory system against a high-volume unstructured system on the same tasks. If the unstructured system consistently outperforms, this assumption is wrong.

**Status:** Partially tested in the existing OSIRIS implementation, where structured PerformanceMemory exists but is not the sole learning mechanism.

---

### A-004: Trading Is the Best First Validation Domain

**Statement:** Financial trading provides the optimal environment for developing and validating criterion before expanding to other domains.

**Why we believe it:** Trading has fast feedback (hours to days), unambiguous outcomes (profit/loss), objective measurement, clear consequence chains, and abundant data.

**Supporting evidence:** Trading is widely used as a testbed for reinforcement learning, pattern recognition, and decision systems. It is arguably the most measurable complex decision domain.

**Contradicting evidence:** Trading may be too narrow. The skills developed in trading may not transfer. The fast feedback may train the system for short-term thinking that harms long-term criterion.

**Confidence:** High

**Impact if false:** **Medium.** If trading is not the best validation domain, the project should identify a better one. Some other domain (prediction markets, sports betting, weather prediction) may offer better properties.

**Falsification method:** Demonstrate that the system develops criterion faster in a different domain than it does in trading, using the same learning architecture.

**Status:** Accepted as a working assumption. Not formally tested against alternatives.

---

### A-005: Consequences Emerge Through Clusters

**Statement:** Meaningful consequences are not produced by single events but by clusters of related events that, taken together, point toward a possible future state.

**Why we believe it:** The most reliable predictions in science, economics, and markets come from converging evidence, not single indicators. Multiple weak signals are more reliable than one strong signal.

**Supporting evidence:** Bayesian reasoning shows that multiple independent pieces of evidence produce more reliable conclusions than any single piece. The insurance, intelligence, and medical diagnosis industries all depend on converging evidence.

**Contradicting evidence:** Some significant consequences are triggered by single events (assassinations, natural disasters, technological breakthroughs). However, these are often unpredictable by nature — they may be outside the scope of any detection system.

**Confidence:** Medium-High

**Impact if false:** **High.** If consequences emerge from single events rather than clusters, the cluster intelligence concept is misdirected.

**Falsification method:** Demonstrate that single-event predictions consistently outperform cluster-based predictions across a broad set of domains.

**Status:** Untested. The current OSIRIS implementation does not have explicit cluster intelligence.

---

### A-006: Learning Transfers Between Domains

**Statement:** Criterion developed in one domain (trading) transfers to other domains (creation, entrepreneurship) through shared underlying principles of consequence detection and evidence evaluation.

**Why we believe it:** Many cognitive skills transfer between domains — pattern recognition, probabilistic reasoning, decision under uncertainty. The mechanisms of learning are domain-general even if the knowledge is domain-specific.

**Supporting evidence:** Expertise in one analytical domain often aids performance in another. Chess players excel at certain strategic games. Traders often succeed in prediction markets. The structure of the OODA loop is domain-independent.

**Contradicting evidence:** Most expertise is domain-specific. Grandmasters at chess are not grandmasters at poker. Domain transfer is notoriously difficult. The feedback structures of trading, creation, and entrepreneurship are very different (fast vs slow, quantitative vs qualitative).

**Confidence:** Low-Medium

**Impact if false:** **High.** If learning does not transfer, each profile requires independent criterion development, multiplying the required experience by the number of profiles.

**Falsification method:** Develop criterion in trading, then measure performance in creation or entrepreneurship. If performance is at chance levels despite trading expertise, transfer has not occurred.

**Status:** Untested. This is one of the highest-risk assumptions and should be prioritized for validation.

---

### A-007: Explicit Hypotheses Outperform Implicit Intuition

**Statement:** Systems that form, track, and test explicit hypotheses develop better criterion than systems that rely on implicit pattern recognition or intuition.

**Why we believe it:** The scientific method — explicit hypothesis formation and testing — is the most successful knowledge-generation process ever developed. Explicit hypotheses allow for error decomposition, which enables targeted improvement.

**Supporting evidence:** The success of science. The effectiveness of structured decision-making in medicine, engineering, and military operations. The failure of intuition in domains with noisy feedback (Kahneman & Tversky).

**Contradicting evidence:** Many successful trading systems operate on pure pattern recognition without explicit hypotheses. Deep learning systems learn implicit representations that outperform explicit rule-based systems in many domains.

**Confidence:** Medium

**Impact if false:** **Medium.** If implicit intuition is superior, the project should invest in learned representations rather than explicit hypothesis structures.

**Falsification method:** Compare an explicit hypothesis-tracking system against an implicit pattern-recognition system on the same tasks. If the implicit system consistently outperforms, this assumption is weakened.

**Status:** Untested. The current OSIRIS system has partial hypothesis tracking (conviction, evidence in metadata) but not fully explicit hypotheses.

---

### A-008: Historical Outcomes Improve Future Decisions

**Statement:** Recording and analyzing past outcomes — both successes and failures — improves the quality of future decisions.

**Why we believe it:** Learning from experience is a fundamental cognitive mechanism. Every field of human expertise depends on accumulated experience. Systems that ignore history repeat errors.

**Supporting evidence:** The existence of learning curves in every domain of expertise. The success of experience-based systems in medicine, law, engineering. The universal human practice of keeping records.

**Contradicting evidence:** Survivorship bias. Hindsight bias. The tendency to overfit to past patterns that do not repeat. Many historical lessons are context-dependent and may mislead when applied to new situations.

**Confidence:** Medium-High

**Impact if false:** **Critical.** If historical outcomes do not improve decisions, the entire learning architecture is misdirected.

**Falsification method:** Show that decision quality correlates negatively with the amount of historical outcome data available, after controlling for other factors.

**Status:** Partially validated. The OSIRIS PerformanceMemory and DirectionController both use historical outcomes to inform decisions, and the system functions correctly.

---

### A-009: Architecture Should Follow Philosophy

**Statement:** The system's architecture should be derived from its philosophical principles, not from convenience, fashion, or technological availability.

**Why we believe it:** Philosophy defines what the system should do. Architecture defines how it does it. If the how drives the what, the system serves its implementation rather than its purpose.

**Supporting evidence:** The most enduring systems in science and engineering are those designed around first principles. Systems designed around available technology become obsolete when technology changes.

**Contradicting evidence:** Practical constraints often force philosophical compromises. A perfect architecture that cannot be built is useless. There is a tension between philosophical purity and operational viability.

**Confidence:** High

**Impact if false:** **Medium.** If architecture should not follow philosophy, the project loses its primary design heuristic, but may gain in practical flexibility.

**Falsification method:** Demonstrate that a system designed for practical convenience consistently outperforms a philosophy-driven system over long time horizons.

**Status:** Accepted as a working principle. Integrated into Design Principles and Constitution.

---

### A-010: The Scientific Method Applies to System Design

**Statement:** Hypotheses about system behavior should be formed, tested, and evaluated using the same rigor as scientific hypotheses.

**Why we believe it:** The scientific method is the most reliable error-correction process known. Applying it to system design prevents dogmatic attachment to untested ideas.

**Supporting evidence:** The success of evidence-based medicine, evidence-based policy, and any field that adopted scientific rigor. The failure of systems designed on intuition without validation.

**Contradicting evidence:** The scientific method is slow. In fast-moving domains, rigorous testing may delay deployment past the window of opportunity. Some knowledge is tacit and cannot be formalized into testable hypotheses.

**Confidence:** High

**Impact if false:** **Medium.** If the scientific method does not apply, the project needs an alternative error-correction mechanism.

**Falsification method:** Demonstrate that a system designed through intuition and rapid iteration consistently outperforms a hypothesis-driven system over time.

**Status:** Accepted as a working principle. Integrated into Project Constitution.

---

## Foundational Assumptions Summary

| ID | Statement | Confidence | Impact if False | Status |
|----|-----------|------------|-----------------|--------|
| A-001 | World produces detectable consequences | Medium | Critical | Untested |
| A-002 | Criterion compounds through experience | Medium | High | Untested |
| A-003 | Memory quality > memory quantity | Medium-High | Medium | Partially tested |
| A-004 | Trading is best validation domain | High | Medium | Accepted |
| A-005 | Consequences emerge through clusters | Medium-High | High | Untested |
| A-006 | Learning transfers between domains | Low-Medium | High | Untested |
| A-007 | Explicit hypotheses > implicit intuition | Medium | Medium | Untested |
| A-008 | Historical outcomes improve decisions | Medium-High | Critical | Partially tested |
| A-009 | Architecture follows philosophy | High | Medium | Accepted |
| A-010 | Scientific method applies to design | High | Medium | Accepted |

*Every assumption in this document is provisional. None is above evidence.*
