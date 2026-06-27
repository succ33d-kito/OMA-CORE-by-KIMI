# Research Backlog

*Research items separated from implementation. Research becomes implementation only after sufficient evidence exists.*

---

## How to Read This Document

| Field | Meaning |
|-------|---------|
| **ID** | Unique identifier |
| **Question** | The research question |
| **Motivation** | Why this matters |
| **Expected impact** | What would change if answered |
| **Dependencies** | What is needed before this can be researched |
| **Priority** | Low / Medium / High / Critical |
| **Current evidence** | What we know so far |
| **Validation experiment** | How to test the hypothesis |
| **Exit criteria** | When this research is complete |
| **Status** | Open / In Progress / Concluded |

---

## Criterion

### R-001: Criterion Measurement Framework

**Question:** How should criterion be measured?

**Motivation:** Without measurement, criterion is a philosophical concept, not an operational one. The project needs a validated measurement framework before criterion can be treated as a primary metric.

**Expected impact:** Would enable quantitative evaluation of the system's core purpose.

**Dependencies:** None — this is foundational research.

**Priority:** Critical

**Current evidence:** The Criterion document proposes seven conceptual levels but no measurement methodology. Self-review of first-principles documents identified this as a high-risk gap.

**Validation experiment:** Develop a candidate measurement battery drawing from psychometrics, expertise research, and calibration theory. Validate it against long-term decision quality across multiple domains.

**Exit criteria:** A published measurement framework with at least three validated dimensions, tested for reliability and predictive validity.

**Status:** Open

---

### R-002: Criterion Development Timeline

**Question:** How long does criterion take to develop to a practically useful level?

**Motivation:** Sets expectations for validation. If criterion requires years of data, early evaluation must use proxy metrics.

**Expected impact:** Would inform milestone planning and evaluation methodology.

**Dependencies:** R-001 (criterion measurement framework)

**Priority:** High

**Current evidence:** Human expertise typically requires ~10,000 hours. Machine learning systems can require millions of examples. The OSIRIS system has hundreds of cycles and single-digit trades — almost certainly insufficient.

**Validation experiment:** Track criterion-relevant metrics continuously from system inception. Identify the inflection point where improvement becomes detectable above noise.

**Exit criteria:** An empirically derived estimate of the minimum experience required for detectable criterion.

**Status:** Open

---

### R-003: Criterion Persistence Under Regime Change

**Question:** Does criterion survive market regime changes? Or does criterion developed in one regime become misleading in another?

**Motivation:** If criterion does not survive regime changes, the system needs regime detection and criterion adaptation mechanisms.

**Expected impact:** Would determine whether criterion can be treated as a stable asset or requires continuous recalibration.

**Dependencies:** R-001 (criterion measurement framework)

**Priority:** High

**Current evidence:** Financial strategies often decay when market regimes change. However, some principles (risk management, position sizing, behavioral patterns) appear regime-independent. The distribution between regime-dependent and regime-independent knowledge is unknown.

**Validation experiment:** Develop criterion before a regime change (bull to bear, low vol to high vol). Measure whether criterion quality is maintained, degraded, or improved after the transition.

**Exit criteria:** A documented relationship between regime stability and criterion persistence, with recommendations for adaptation mechanisms.

**Status:** Open

---

## Learning

### R-004: Optimal Memory Structure

**Question:** What memory structure maximizes learning efficiency for criterion development?

**Motivation:** The project assumes memory quality matters more than memory quantity, but the optimal structure is unknown.

**Expected impact:** Would guide the next major memory architecture decision.

**Dependencies:** None

**Priority:** High

**Current evidence:** The OSIRIS system uses a simple memory structure (trade lists, agent records, opinion outcomes). Explicit hypothesis linking does not exist. It is unknown whether richer structure would improve learning.

**Validation experiment:** Compare multiple memory architectures (flat, hypothesis-linked, graph-based, time-decayed) on criterion development speed and quality.

**Exit criteria:** An empirically supported recommendation for memory architecture, with measured trade-offs between complexity and learning efficiency.

**Status:** Open

---

### R-005: Evidence Decay Profile

**Question:** What is the optimal decay rate for evidence? How quickly should old evidence be discounted?

**Motivation:** Without evidence decay, the system treats ten-year-old patterns as equally relevant as yesterday's. With too much decay, the system forgets valuable lessons.

**Expected impact:** Would inform evidence weighting and memory management.

**Dependencies:** None

**Priority:** Medium

**Current evidence:** The OSIRIS system does not have explicit evidence decay. PerformanceMemory and DirectionController use rolling windows (last 20 trades for direction control), which is a form of evidence decay. The optimal window size is unknown.

**Validation experiment:** Compare fixed-window, time-decayed, and event-count-decayed evidence weighting on decision quality across different market conditions.

**Exit criteria:** An evidence decay strategy that demonstrably outperforms no-decay baselines.

**Status:** Open

---

### R-006: Error Classification Utility

**Question:** Does explicit error classification improve learning speed compared to simple win/loss recording?

**Motivation:** The Failure Intelligence concept assumes classification is valuable. This should be validated before investing in classification infrastructure.

**Expected impact:** Would determine whether to invest in failure classification systems.

**Dependencies:** None

**Priority:** Medium

**Current evidence:** The OSIRIS system classifies exit reasons (stop loss, take profit, time expiry) but does not classify failure types (wrong hypothesis, wrong timing, poor execution).

**Validation experiment:** Compare two systems — one with simple win/loss recording, one with multi-dimensional error classification — on criterion development speed.

**Exit criteria:** A statistically significant demonstration that error classification improves learning speed or quality.

**Status:** Open

---

## Consequence

### R-007: Consequence Detection Accuracy Baseline

**Question:** What is the baseline accuracy of consequence detection using the current OSIRIS architecture?

**Motivation:** The foundational assumption (A-001) is untested. A baseline measurement is needed to evaluate whether improvements are meaningful.

**Expected impact:** Would provide the current performance baseline and inform whether consequence detection is viable.

**Dependencies:** None — can be measured with existing data.

**Priority:** Critical

**Current evidence:** The OSIRIS system generates signals with ~49% directional accuracy at 24 hours (synthetic data). This is near chance. Real-market accuracy may differ. It is unknown whether this constitutes consequence detection or noise trading.

**Validation experiment:** Analyze all historical trades to measure whether signals correspond to identifiable consequences (detectable clusters of events that preceded the trade). Compare consequence-linked trades against non-consequence-linked trades.

**Exit criteria:** A documented baseline for consequence detection accuracy, with confidence intervals and identified failure modes.

**Status:** Open

---

### R-008: Single-Event vs Cluster-Event Detection

**Question:** Are cluster-based consequences more reliable than single-event consequences?

**Motivation:** The cluster hypothesis (A-005) is central to the theory but untested.

**Expected impact:** Would validate or invalidate the cluster intelligence concept.

**Dependencies:** R-007 (consequence detection baseline)

**Priority:** High

**Current evidence:** No evidence exists. The OSIRIS system does not have explicit cluster intelligence.

**Validation experiment:** Compare detection accuracy for consequences derived from single events vs consequences derived from multiple converging events.

**Exit criteria:** A documented relationship between cluster size/diversity and consequence detection accuracy.

**Status:** Open

---

## Capital Allocation

### R-009: Optimal Position Count

**Question:** What is the optimal number of simultaneous positions for criterion development?

**Motivation:** The current limit of 3 positions is an arbitrary starting point. The optimal count for learning is unknown.

**Expected impact:** Would inform capacity limit configuration for future validation.

**Dependencies:** None

**Priority:** Medium

**Current evidence:** Extended Demo telemetry shows that with 3 positions, the system spends most of its time at capacity and rejects most signals. This may be good (forces prioritization) or bad (limits learning opportunities).

**Validation experiment:** Compare criterion development speed with different position limits (1, 3, 5, 10). Measure both decision quality and learning efficiency.

**Exit criteria:** An empirically supported recommendation for position limits that balance learning and performance.

**Status:** Open

---

### R-010: Replacement Decision Framework

**Question:** Can replacement decisions improve portfolio quality compared to first-in-first-out position management?

**Motivation:** The Execution and Capital Allocation thesis proposes replacement as a key mechanism. Its value needs validation.

**Expected impact:** Would determine whether to invest in replacement infrastructure.

**Dependencies:** None

**Priority:** Medium

**Current evidence:** No evidence exists. The OSIRIS system does not support replacement.

**Validation experiment:** Simulate replacement-based position management against fixed-position management using historical data. Measure portfolio quality differences.

**Exit criteria:** A demonstrated improvement in portfolio quality from replacement decisions, with documented conditions where replacement is beneficial vs harmful.

**Status:** Open

---

## Cluster Intelligence

### R-011: Event Correlation Detection

**Question:** Can the system automatically detect meaningful correlations between events, or must correlations be predefined?

**Motivation:** Cluster intelligence depends on detecting event relationships. The method for doing so is unknown.

**Expected impact:** Would determine the feasibility of automatic cluster detection.

**Dependencies:** R-007 (consequence detection baseline)

**Priority:** Medium

**Current evidence:** The OSIRIS system does not correlate events across domains. Each agent operates independently. Cross-agent correlation is not implemented.

**Validation experiment:** Build a correlation detection layer that analyzes event streams for statistical relationships. Measure whether detected correlations improve consequence detection accuracy.

**Exit criteria:** A demonstrated ability to detect non-obvious event correlations that improve prediction accuracy.

**Status:** Open

---

## Failure Intelligence

### R-012: Failure Type Distribution

**Question:** What is the distribution of failure types in the current system?

**Motivation:** Without knowing what types of errors the system makes, targeted improvement is impossible.

**Expected impact:** Would identify the system's most common failure modes and prioritize improvement efforts.

**Dependencies:** None — can be analyzed from existing data.

**Priority:** Medium

**Current evidence:** The OSIRIS system records exit reasons but does not classify failures by type. It is unknown whether most losses come from wrong hypotheses, wrong timing, or poor execution.

**Validation experiment:** Analyze all closed trades and classify each loss by failure type. Document the distribution.

**Exit criteria:** An empirically derived failure type distribution for the current system.

**Status:** Open

---

## Decision Quality

### R-013: Decision Decomposition

**Question:** Can decision quality be decomposed into components (perception, judgment, execution, timing)?

**Motivation:** Decomposition enables targeted improvement — fixing the specific component that caused the error.

**Expected impact:** Would enable more precise learning from outcomes.

**Dependencies:** R-012 (failure type distribution)

**Priority:** Medium

**Current evidence:** The decision decomposition is theoretical. No operational decomposition exists in the current system.

**Validation experiment:** Develop a decision decomposition framework. Test whether decomposed feedback produces faster improvement than holistic feedback.

**Exit criteria:** A validated decision decomposition framework with demonstrated improvement benefits.

**Status:** Open

---

## Research Backlog Summary

| ID | Question | Category | Priority | Status |
|----|----------|----------|----------|--------|
| R-001 | Criterion measurement framework | Criterion | Critical | Open |
| R-002 | Criterion development timeline | Criterion | High | Open |
| R-003 | Criterion persistence under regime change | Criterion | High | Open |
| R-004 | Optimal memory structure | Learning | High | Open |
| R-005 | Evidence decay profile | Learning | Medium | Open |
| R-006 | Error classification utility | Learning | Medium | Open |
| R-007 | Consequence detection accuracy baseline | Consequence | Critical | Open |
| R-008 | Single-event vs cluster-event detection | Consequence | High | Open |
| R-009 | Optimal position count | Capital Allocation | Medium | Open |
| R-010 | Replacement decision framework | Capital Allocation | Medium | Open |
| R-011 | Event correlation detection | Cluster Intelligence | Medium | Open |
| R-012 | Failure type distribution | Failure Intelligence | Medium | Open |
| R-013 | Decision decomposition | Decision Quality | Medium | Open |

**Total research backlog:** 13 items (2 Critical, 4 High, 7 Medium)

*Research items are NOT implementation tasks. They become implementation only after sufficient evidence exists.*
