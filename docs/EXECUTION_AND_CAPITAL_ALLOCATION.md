# Execution & Capital Allocation

## A Strategic Thesis for O.M.A.-C.O.R.E.

*Version 1.0 — June 2026*

---

## 1. Executive Summary

Generating opportunities is one problem. Allocating capital is a fundamentally different one.

The current OSIRIS pipeline excels at the first: events enter, agents analyze, council decides, signals emerge. The bottleneck is not signal generation — it is execution capacity.

Extended Demo telemetry reveals a clear pattern. Signals continue to flow. The system remains healthy. No runtime errors occur. Yet every cycle after position capacity is reached follows the same rhythm: signals are generated, examined, and rejected. The engine answers a simple question — *"Can I open another trade?"* — and receives the same answer until a position closes.

This is not a bug. It is an architectural boundary point. The system has reached the limit of its current execution philosophy.

The thesis of this document is that:

**Capital is a scarce resource. Every opportunity competes for it. The execution engine should evolve from a binary gate — can I execute, yes or no — to an allocation system that continuously evaluates which active opportunity most deserves the next unit of capital.**

This shift transforms execution from a plumbing concern into a core intelligence problem. It connects directly to the Criterion and Consequence thesis already documented in this repository. The same accumulated judgment that detects consequences should also decide which consequences are worth acting on when capital is limited.

---

## 2. Current Architecture

### 2.1 The Signal Path

The current execution flow follows a linear chain:

```
Market Data
      ↓
Event Generation
      ↓
MarketAgent → candidate-based scoring → AgentOpinion
RiskAgent  → volatility assessment → AgentOpinion
      ↓
AgentCouncil → weighted voting → CouncilDecision
      ↓
PaperTradingEngine.process_decision()
      ↓
  Guard Layer 1: CapitalGuard.is_trading_allowed() → kill switch
  Guard Layer 2: DirectionController → direction disabled?
  Guard Layer 3: CapitalGuard.guard_mode() → EMERGENCY/HALT?
  Guard Layer 4: CrashDetector.crash_mode() → PANIC/falling knife?
  Guard Layer 5: Metadata validation → valid signal?
      ↓
TradeSignal constructed (price, stop, target, conviction, risk)
      ↓
PaperTradingEngine.execute_signal()
      ↓
  Capacity check: len(positions) >= max_open_positions?
  Capacity check: remaining_capacity >= signal size?
      ↓
Trade opened OR execution block recorded
```

### 2.2 Guards and Their Role

Each guard answers a binary safety question:

| Guard | Question It Answers |
|-------|-------------------|
| CapitalGuard | Is trading allowed at all? (kill switch, drawdown limits, consecutive losses) |
| DirectionController | Is this direction currently viable? (rolling win rate below 25%) |
| CrashDetector | Is the market in a crash regime? (panic/emergency blocks all or long) |
| KnifeDetector | Is this particular buy a falling knife? (only used within crash guard) |
| GapRiskEngine | How wide should stops be? (gap risk multipliers) |
| SlippageEngine | What is the expected execution cost? (spread + slippage) |

All guards are independent. None considers what other opportunities exist. None compares the current signal against active positions. None asks whether replacing an existing position would be more valuable than rejecting a new signal.

### 2.3 Capacity Limits

The execution engine has one capacity mechanism: `max_open_positions`, set to 3 in the Demo Harness. The check is:

```python
if len(self.positions) >= self.max_open_positions:
    return None  # → execution block recorded
```

There is no concept of partial replacement, priority ranking, or portfolio-level optimization. The system reaches capacity and stays there until a position closes via stop loss, take profit, or time expiry.

### 2.4 Position Tracking

The engine tracks positions as a simple list. Each position has a size, entry price, stop loss, take profit, and time horizon. Positions are closed independently — `check_positions()` iterates the list and closes any that hit their exit conditions. There is no mechanism for early position review or opportunity-based replacement.

### 2.5 Performance Memory

After a trade closes, attribution flows to:
- `PerformanceMemory.record_trade()` — stores the trade for querying
- `PerformanceMemory.record_opinion_outcome()` — tracks which agent opinions were correct
- `DirectionController.record_trade()` — updates rolling win rate
- `CapitalGuard.record_trade_result()` — updates drawdown and consecutive loss counters

This data is used for future council weighting but does **not** influence real-time capital allocation decisions.

---

## 3. Observed Behaviour

### 3.1 Telemetry Evidence

Extended Demo telemetry across 153 cycles (50 from the original session, 103 from the 7-day smoke run) reveals a consistent pattern:

**Phase 1 — Capital Accumulation (cycles 1–3):** The system opens positions until it reaches capacity. Signals are generated, guards approve, trades execute. Open positions rise from 0 to 3.

**Phase 2 — Capacity Saturation (cycles 4–103):** Open positions remain at 3. Each cycle generates 0–2 signals. Most signals are blocked by execution capacity. Guard blocks occur when no signal passes `process_decision()`. Execution blocks occur when a signal passes guards but `execute_signal()` rejects it due to `max_open_positions`.

**Phase 3 — Occasional Replacement (cycles 75, 76, 95):** A position closes (stop loss or take profit), capacity opens, and the next signal executes. The cycle repeats.

Key metrics:

| Metric | Value |
|--------|-------|
| Total cycles | 153 |
| Runtime errors | 0 |
| Data failures | 0 |
| Signals generated | 100+ |
| Trades opened | ~10 |
| Guard blocks | ~70 |
| Execution blocks | ~150+ |
| Final guard mode | normal |
| Final crash mode | none |

### 3.2 What This Tells Us

The system functions correctly. Every component works. No failures occur. But the execution bottleneck is **policy-driven, not quality-driven.**

Signals continue to be generated with valid conviction scores. The council continues to produce decisions. The guards find no reason to block — the market is normal, crash mode is none, guard mode is normal. Yet the signal is rejected because three positions already exist.

The question is not whether the third position is worth holding. The question is whether the new opportunity is **more** worth holding than the weakest existing position.

The current architecture cannot answer this question.

---

## 4. The Real Problem

The current execution engine asks:

> *"Can I open another trade?"*

The future execution engine should ask:

> *"Does this opportunity deserve capital more than my existing positions?"*

These are fundamentally different questions.

The first is a **capacity check**. It examines one resource (max open positions) and returns a boolean. It has no concept of trade-offs, opportunity cost, or relative value. It treats all open positions as equally worth holding and all new signals as equally worth rejecting.

The second is an **allocation decision**. It requires:
- A value estimate for the new opportunity
- A value estimate for each existing position
- A comparison framework
- A replacement threshold
- A confidence calibration for each estimate

The first question is easy to implement. The second is hard — but it is the difference between a system that executes signals and a system that **allocates capital intelligently.**

The telemetry data confirms this. Every cycle after saturation, the system generates signals with conviction scores in the 58–64 range, evaluates them through the same guard pipeline, and rejects them for the same reason. The opportunity cost of staying with the current three positions is never measured.

---

## 5. Capital Is Limited

Capital is not just money. In the O.M.A.-C.O.R.E. framework, limited resources include:

| Resource | Description | Limit |
|----------|-------------|-------|
| **Capital** | Cash available for allocation | Initial capital + accumulated PnL |
| **Risk budget** | Maximum acceptable drawdown | 35% (HALT threshold) |
| **Margin** | Capital consumed by open positions | Per-position allocation |
| **Exposure** | Total market exposure at any time | Sum of all position sizes |
| **Execution slots** | Maximum simultaneous positions | Currently 3 |
| **Attention** | Monitoring bandwidth per position | Implicit — more positions = less attention per position |
| **Time** | Duration capital is committed | Per-position time horizon |

Every opportunity competes for these resources. Opening position A means not opening position B. Keeping position C open through a drawdown means not having that capital available when a better opportunity appears.

The current system treats these as independent constraints checked at different points in the pipeline. Capital is checked at sizing. Execution slots are checked at execution. Drawdown is checked at the guard level. There is no unified view of resource competition.

---

## 6. Execution Philosophy

The execution engine should evolve through three stages:

### Stage 1 — Binary Gate (Current)

```
Signal arrives → can I execute? → yes/no
```

Every signal is evaluated independently. Capacity is a hard wall. No comparison occurs.

### Stage 2 — Ranked Queue

```
Signal arrives → score signal → compare to queue → best N execute
```

Signals are ranked and the top N execute. If positions reach capacity, the weakest position may be replaced. This requires an opportunity queue and a position scoring mechanism.

### Stage 3 — Continuous Allocation

```
Opportunity arrives → score → compare to portfolio →
  replace? reduce? increase? hold? wait? ignore?
```

The system continuously evaluates its portfolio against new information. Every new opportunity triggers a portfolio review. Every position is held subject to being outranked by a better use of capital.

The direction of evolution is:

**Execute every valid signal → Allocate scarce resources to the highest expected consequences.**

This connects directly to the Criterion thesis. The same criterion that judges consequences should judge which consequences are worth acting on. The system's accumulated judgment — built from thousands of hypotheses, decisions, outcomes, and corrections — should inform not only what to trade, but what to **prioritize.**

---

## 7. Opportunity Competition

### 7.1 Current Flow

```
Signal → Guard Check → Capacity Check → Execute or Reject
```

There is no comparison step. Each signal exists in isolation.

### 7.2 Future Flow

```
Signal
  ↓
Opportunity Ranking (score: conviction × evidence × alignment)
  ↓
Portfolio Comparison (new opportunity vs weakest current position)
  ↓
Replacement Decision (does new opportunity exceed replacement threshold?)
  ↓
Execution (open new, or replace, or hold, or wait)
```

This requires:

**An opportunity ranking function.** Not just conviction — a richer score that includes evidence quality, cluster strength, macro alignment, and time horizon fit.

**A position scoring function.** Every open position has an expected remaining value. This can be estimated from current price relative to target, time remaining, and confidence in the original thesis.

**A comparison framework.** A rule or model that determines whether the new opportunity's score exceeds the weakest position's score by a sufficient margin to justify replacement costs (slippage, spread, timing risk).

### 7.3 Why Competition Matters

Without competition, the system fills its slots with the first N signals that pass guards. The quality of positions depends entirely on the order signals arrive. A strong signal on cycle 5 may be locked in while a stronger signal on cycle 50 is rejected — not because it is worse, but because the slots are full.

With competition, the portfolio continuously improves. Capital flows toward the highest-conviction opportunities. The system never settles for "good enough" while a better opportunity exists.

---

## 8. Replacement Concept

Replacement is the mechanism by which a new opportunity takes capital from an existing position.

### 8.1 When Replacement Makes Sense

```
Current position expected value: 58
New opportunity expected value:   91
Replacement threshold:            15 points
→ Replace (91 - 58 = 33 > 15)
```

The threshold accounts for:
- Transaction costs (slippage, spread on both close and open)
- Timing risk (the new opportunity may not fill at expected price)
- Opportunity cost of the current position's remaining upside

### 8.2 When Replacement Does Not Make Sense

```
Current position expected value: 85
New opportunity expected value:   78
→ Do not replace (new opportunity is worse)
```

```
Current position expected value: 60
New opportunity expected value:   68
Margin: 8 < threshold: 15
→ Do not replace (not enough edge to justify costs)
```

### 8.3 Replacement Should Depend on Evidence, Not Profit Alone

A position that is slightly losing but has strong hypothesis support may be worth keeping. A position that is slightly winning but whose hypothesis has been invalidated may be worth replacing.

This connects to hypothesis tracking. If the original thesis for an existing position is weakening, the position's expected value declines regardless of current PnL. If a new opportunity has stronger cluster support, higher evidence quality, or better macro alignment, it may deserve capital even if its raw conviction score is similar.

Replacement is not a mechanical formula. It is a **criterion decision.**

---

## 9. Opportunity Lifecycle

An opportunity in the future system should follow a structured lifecycle:

```
Detected
  ↓
Scored (conviction × evidence × alignment × timing)
  ↓
Queued (ranked among all active opportunities)
  ↓
Executed (capital allocated, position opened)
  ↓
Monitored (tracked against hypothesis)
  ↓
Updated (hypothesis re-evaluated as new evidence arrives)
  ↓
Closed (exit conditions met OR replaced OR hypothesis invalidated)
  ↓
Learned (outcome recorded, hypothesis evaluated, criterion updated)
```

### 9.1 Why Monitoring and Updating Matter

In the current system, a position is opened and then monitored for exit conditions. There is no mechanism to re-evaluate the position's hypothesis mid-life. If new evidence contradicts the original thesis, the position continues until stopped out.

In the future system, every open position should have an active hypothesis. New events that affect that hypothesis trigger a re-evaluation. If the hypothesis weakens, position size may be reduced or the position may be replaced. If the hypothesis strengthens, conviction increases.

This makes the portfolio dynamic not just at entry but throughout the position's life.

### 9.2 Why the Learn Stage Is Critical

The lifecycle does not end at close. It ends at learning. Every closed opportunity — whether it won or lost — produces a structured lesson:

- Was the original hypothesis correct?
- Was the evidence sufficient?
- Was the timing accurate?
- Was the execution well-calibrated?
- What would the system do differently next time?

These lessons accumulate into criterion.

---

## 10. Capital Allocation Criteria

Future capital allocation should consider multiple dimensions. These are listed as **conceptual dimensions** — not formulas to implement today.

| Dimension | What It Captures |
|-----------|-----------------|
| **Expected value** | Conviction-adjusted return estimate |
| **Confidence** | How certain the system is about this estimate |
| **Risk** | Position-level risk (ATR, volatility, stop distance) |
| **Correlation** | How this opportunity relates to existing positions |
| **Portfolio diversification** | Whether this improves the portfolio's risk profile |
| **Time horizon** | How long capital will be committed |
| **Liquidity** | How easily the position can be entered and exited |
| **Macro alignment** | Whether macro conditions support this opportunity |
| **Cluster strength** | How many independent signals converge on this consequence |
| **Hypothesis quality** | How well-structured and testable the hypothesis is |
| **Evidence quality** | How reliable the supporting evidence is |
| **Criterion alignment** | Whether this matches what the system has learned to recognize |

These dimensions should not be naively summed. The relationship between them is context-dependent. In a calm market, diversification may matter more. In a volatile market, liquidity and risk dominate.

The key insight is that capital allocation is a **multi-dimensional optimization problem**, not a single-threshold gate.

---

## 11. Criterion Connection

The Criterion thesis states that O.M.A.-C.O.R.E.'s purpose is to develop operational criterion over time — the accumulated ability to judge what matters.

Capital allocation is where criterion meets action.

Every allocation decision is a test of criterion:
- Did the system correctly identify which opportunity deserved capital?
- Did the evidence support the decision?
- Did the system learn from the outcome?

When capital is allocated well, criterion is validated. When capital is allocated poorly, criterion should be updated. The feedback loop is direct and measurable.

This changes the validation question. The current system asks: *"Was this trade profitable?"* The criterion-informed system asks: *"Was this allocation justified by the evidence available at the time?"*

A trade can be profitable by luck and teach nothing. A trade can be unprofitable but justified — and teach a calibrated lesson about risk. The difference is whether the system can distinguish between the two.

**Execution should not optimize for opening trades. It should optimize for allocating scarce capital according to accumulated criterion.**

---

## 12. Future Execution Engine

A future execution engine should be capable of asking multiple questions about each opportunity:

| Question | Meaning |
|----------|---------|
| **Should I execute?** | Open a new position with this opportunity |
| **Should I wait?** | Queue the opportunity, execute later if evidence strengthens |
| **Should I replace?** | Close the weakest position and open this one |
| **Should I reduce?** | Scale down an existing position to free capital for this |
| **Should I increase?** | Add to an existing position that aligns with this opportunity |
| **Should I ignore?** | The opportunity does not meet the threshold |
| **Should I monitor?** | Keep watching — may become actionable with more evidence |

This is a richer decision space than the current binary execute/reject. Each question corresponds to a different relationship between the new opportunity and the existing portfolio.

The engine does not need to implement all of these immediately. But the architecture should support evolving toward them.

---

## 13. Future Metrics

As the execution engine evolves, new metrics become meaningful:

| Metric | Definition |
|--------|------------|
| **Execution Efficiency** | Capital deployed ÷ capital available (utilization rate) |
| **Capital Utilization** | Percentage of available capital that is productively deployed |
| **Opportunity Capture Rate** | Profitable opportunities acted upon ÷ profitable opportunities that existed in the observed window |
| **Replacement Accuracy** | Percentage of replacements that improved portfolio value |
| **Missed Opportunity Rate** | Opportunities that became profitable but were not captured |
| **Capital Rotation Quality** | Average quality improvement per replacement cycle |
| **Portfolio Opportunity Quality** | Average conviction × evidence score of active positions |
| **Criterion Alignment** | Correlation between allocation decisions and subsequent criterion validation |

These metrics are not for immediate implementation. They are documented to guide how validation should expand beyond raw PnL and win rate.

---

## 14. Architectural Implications

This thesis affects multiple future systems:

| System | Implication |
|--------|-------------|
| **Portfolio Engine** | Must track position-level expected value, not just entry/exit state |
| **Execution Engine** | Must support comparison, ranking, replacement, and multi-question decisions |
| **Learning Engine** | Must attribute outcomes to allocation decisions, not just signal quality |
| **Criterion** | Must inform allocation thresholds and replacement rules |
| **Hypothesis Tracking** | Must keep hypotheses alive for open positions and update them with new evidence |
| **Consequence Engine** | Must estimate consequence quality as an input to allocation scoring |
| **Agent Council** | Must provide opportunity rankings, not just binary decisions |

Capital allocation becomes a **core intelligence problem** rather than an execution detail. It sits at the intersection of:

- **Perception** — what opportunities exist
- **Judgment** — which opportunities are most valuable
- **Action** — how to deploy capital optimally
- **Learning** — whether the allocation was justified

Each of these maps to a component that already exists in embryo form. The thesis shows how they connect.

---

## 15. Near-Term Recommendation

**No implementation should happen yet.**

The current execution engine remains fully valid for MVP validation. It answers the questions that need answering at this stage:

1. Can the system generate valid signals? ✅ Yes — demonstrated across thousands of cycles
2. Can the system execute trades safely? ✅ Yes — guards function correctly
3. Can the system track outcomes? ✅ Yes — PerformanceMemory records and attributes
4. Can the system operate continuously? ✅ Yes — smoke run at 103 cycles with 0 errors

The goal of this document is **preserving architectural direction**. When the current execution engine reaches its natural limit — when the question shifts from "can the system execute" to "can the system allocate better" — this thesis provides the conceptual foundation.

**Validation remains the highest priority.** Complete the 7-day smoke run. Complete the 30-day validation. Accumulate outcomes. Let PerformanceMemory build track records. The data from these runs will inform how capital allocation should evolve — and the thesis ensures that evolution has a direction.

---

## 16. Final Principle

The value of O.M.A.-C.O.R.E. will not come from generating the largest number of opportunities.

It will come from consistently recognizing which opportunities deserve scarce capital before the rest of the market does.

The execution engine should not be measured by how many trades it opens.

It should be measured by how well it answers the question that every limited-resource system must eventually face:

*Given that I cannot do everything, what should I do now?*
