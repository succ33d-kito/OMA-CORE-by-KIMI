# CP-8.0 — P0 Economic Baseline Protocol

Status: SEMANTICS_FROZEN / PRE-CP7L / NO NEW ECONOMIC RESULTS SEEN
Branch: work/post-cp7l-prep-20261009

This document freezes the intended economic evaluation semantics before the
modern PAPER accounting layer is implemented and before new economic results
are inspected.

## Scientific state

EDGE=NOT_DEMONSTRATED
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE

This protocol does not authorize promotion, live capital, holdout access,
Knowledge validation, Criterion updates, or policy retuning.

---

# 1. Governing scientific rules

The protocol inherits these repository-level rules:

1. Experimental design must be documented before outcome access.
2. Population membership must be frozen before outcome access.
3. PILOT, DISCOVERY and CONFIRMATION evidence must remain separated.
4. Thresholds must not be chosen after viewing holdout outcomes.
5. Holdout results must not be used for retuning.
6. Missing or unknown values must remain unknown; UNKNOWN != 0.
7. Failures, abstentions and rejected opportunities are preserved.
8. Incomplete provenance means NO LEARNING.
9. Unvalidated Knowledge cannot update Criterion.
10. Economic PnL is not by itself a LearningSignal.
11. A profitable decision is not automatically a good decision.
12. An unprofitable decision is not automatically a bad decision.

---

# 2. Dataset roles and holdout barriers

## PILOT

Purpose:

- plumbing;
- contract verification;
- causal evidence validation;
- protocol feasibility.

PILOT results cannot establish Edge.

## DISCOVERY

Purpose:

- evaluate frozen hypotheses;
- estimate exploratory effect sizes;
- identify failure modes;
- test ablations.

Discovery evidence may reject hypotheses or justify future confirmation.

It cannot establish independent confirmation.

## CONFIRMATION

Confirmation must be isolated from discovery and parameter selection.

Known barriers remain:

- Binance 2024: DISCOVERY context only.
- Binance 2025: prior exposure exists; it must never be represented as a
  pristine never-seen holdout.
- Kraken Q2-2026: remains SEALED_CROSS_EXCHANGE_HOLDOUT unless a separately
  authorized protocol explicitly opens it.

No confirmation dataset may be opened merely because implementation is ready.

---

# 3. Population freeze

Before evaluating economic results, a manifest must freeze:

- protocol identity;
- code baseline;
- dataset role;
- instrument universe;
- decision population;
- temporal range;
- eligibility rules;
- exclusion rules;
- missingness rules;
- causal evidence requirements;
- support snapshots;
- manifest identity.

The manifest must be preserved before outcome access.

Population membership must not depend on:

- future return;
- PnL;
- win/loss;
- Sharpe;
- drawdown;
- profit factor;
- future regime label;
- later availability of better evidence.

---

# 4. Unit of decision

The primary decision unit is one frozen capital-allocation decision produced
without access to future outcome information.

A decision may result in:

- TRADE;
- ABSTAIN;
- DEFER;
- REJECT;
- NO_ORDER.

All states are valid observations.

Trade-producing decisions must not be selected as the only population after
outcomes are known.

---

# 5. Unit of trade

A trade exists only when the modern causal PAPER chain produces a complete:

entry
-> open position
-> lifecycle
-> exit intent
-> exit fill
-> closed position

A signal, OrderIntent, ExecutionEstimate, pending PositionState, or exit intent
alone is not a completed trade.

The authoritative completed PAPER trade boundary is expected to be CP-7L
PaperClosedPosition once CP-7L is published and audited.

---

# 6. Primary horizon

The economic primary horizon must follow the frozen thesis / lifecycle horizon
used to generate the exit decision.

No alternative horizon may be selected because it produces better performance.

If multiple horizons are later investigated, they are separate registered
variants and count toward multiplicity.

No universal numeric horizon is frozen by this document because the current
modern PAPER lifecycle is thesis-driven.

---

# 7. Abstention and cash semantics

ABSTAIN, DEFER, REJECT and NO_ORDER are not failures.

Unallocated capital is a valid portfolio state.

Cash / unallocated risk budget must not be assigned synthetic returns merely to
force comparison.

A strategy is not required to trade in every eligible decision window.

Trade frequency itself is an evaluated consequence, not a success criterion.

---

# 8. Risk authority

Risk authority remains upstream of economic ranking.

Economic performance cannot override a risk rejection.

The existing historical 35% HALT value in older capital-allocation
documentation is not adopted as the CP-8 P0 risk budget.

This document does not change the current operational risk configuration.

Before executable economic qualification, one authoritative P0 risk policy
must be separately frozen by configuration / protocol identity.

No risk parameter may be optimized against confirmation outcomes.

---

# 9. Position sizing

Position size must come from the authoritative upstream allocation lineage.

Accounting may consume size.

Accounting must not choose size.

No economic evaluator may rescale trades after outcomes are known.

Cash remaining after allocation remains cash.

---

# 10. Gross economic result

The future PaperGrossEconomicResult should derive only from the complete modern
closed-position lineage.

Expected primary quantities:

- entry price;
- exit price;
- base quantity;
- entry notional;
- exit notional;
- gross price PnL;
- gross return.

Prices and quantity are SIMULATED PAPER values derived from causal evidence.

Gross PAPER economics are not factual venue account economics.

---

# 11. Cost model

Cost components must preserve epistemic status.

Allowed status vocabulary:

OBSERVED
SIMULATED
CONFIGURED
DERIVED
UNKNOWN
UNSUPPORTED

## Fees

Observed account-scoped fee-rate evidence may support fee calculation.

Without valid causal evidence:

fee_rate = UNKNOWN

A configured fee assumption may be reported only as CONFIGURED.

CONFIGURED must never be relabelled OBSERVED.

## Funding

Observed funding rate is not funding payment.

Funding cashflow requires sufficient causal evidence of:

- funding event;
- exposure at event time;
- applicable quantity/notional;
- mark/basis;
- rate;
- direction/sign;
- timestamps;
- provenance.

Otherwise:

funding_cashflow = UNKNOWN

## Slippage

The current modern PAPER model has no factual venue fill.

Therefore:

observed_slippage = UNKNOWN

Legacy SlippageEngine output may be used only as CONFIGURED scenario analysis.

## Spread

Bid/ask spread may be OBSERVED / DERIVED from causal book evidence.

Spread must not be counted twice if simulated entry/exit fills already use the
executable side of the book.

## Other costs

UNKNOWN unless separately evidenced.

---

# 12. Net economic result

Net PnL must fail closed.

A mandatory unknown cost cannot silently become zero.

If the frozen protocol requires a cost component that is unresolved:

net_pnl = UNKNOWN
net_return = UNKNOWN

Gross metrics may still be reported independently.

Scenario metrics using configured assumptions must be labelled CONFIGURED and
must not be mixed with causal observed economics.

---

# 13. Core economic metrics

For eligible completed PAPER trades, report at minimum:

- number of decisions;
- number of completed trades;
- abstentions;
- deferrals;
- rejections;
- no-order decisions;
- gross PnL where defined;
- gross return where defined;
- net PnL where defined;
- net return where defined;
- cost completeness rate;
- turnover;
- hit rate;
- expectancy;
- profit factor;
- maximum drawdown;
- exposure;
- time in market.

Metric undefined states remain NULL / UNKNOWN.

No infinite profit factor is reported when there are no losses.

No metric may silently exclude losing or incomplete observations to improve
reported performance.

---

# 14. Drawdown

Drawdown must be calculated from one explicitly frozen equity convention.

At minimum distinguish:

- closed-equity drawdown;
- mark-to-market drawdown, if supported later.

Closed-equity drawdown must not be presented as intratrade drawdown.

The chosen primary drawdown convention must be declared before evaluation.

---

# 15. Profit factor

Profit factor is:

sum positive realized eligible economic results
/
absolute sum negative realized eligible economic results

only for the result layer whose completeness requirements are satisfied.

If denominator is zero:

profit_factor = NULL

not infinity.

Gross and net profit factor must never be mixed.

---

# 16. Expectancy

Expectancy must be calculated over the frozen eligible population.

Trade-only expectancy may be reported, but decision-level trade frequency and
abstention frequency must accompany it.

A high trade expectancy with severe selection attrition is not by itself
evidence of superior allocation.

---

# 17. Hit rate

Hit rate is descriptive only.

It must not be used alone to claim Edge.

Zero-return / undefined outcomes must follow a pre-registered classification
rule rather than being assigned opportunistically.

---

# 18. Turnover

Turnover must be computed from actual simulated PAPER allocation / close
lineage, not from signal counts.

Repeated rejected or deferred signals are not turnover.

---

# 19. Calibration

Calibration may be evaluated only where the upstream forecast is a genuine
probabilistic forecast with frozen semantics.

Raw scores, rankings and conviction values must not be treated as calibrated
probabilities without a separate calibration contract.

Uncalibrated forecast != economic probability.

---

# 20. Baselines

P0 must compare the modern system against one or more pre-registered reference
policies.

Reference policies must be labelled synthetic / non-calibrated / non-Edge
where applicable.

No baseline may be chosen after seeing which comparator is easiest to beat.

ReferenceRule / ReferenceForecasts do not become validated Alpha by serving as
baselines.

---

# 21. Statistical uncertainty

Point estimates alone are insufficient for promotion.

Where sample size permits, evaluation should use time-aware uncertainty
estimation.

Preferred approach:

- calendar/time blocks;
- block bootstrap or equivalent dependence-aware method;
- preserved chronological structure.

IID assumptions must not be silently applied to serially dependent trading
observations.

---

# 22. Minimum sample

No universal minimum sample is claimed by the current repository protocol.

The historical MM-H1 threshold of 50 trades per holdout variant is specific to
that experiment and is not promoted here into a universal rule.

Before economic qualification, minimum sample must be frozen using:

- expected effect size;
- variance;
- temporal dependence;
- number of tested variants;
- regime coverage;
- cost uncertainty.

Until then:

SAMPLE_SUFFICIENT=NO

for promotion purposes.

---

# 23. Multiple testing

Every tested variant counts.

This includes changes to:

- thresholds;
- horizons;
- filters;
- mechanics variables;
- regime definitions;
- cost assumptions;
- sizing;
- entry rules;
- exit rules.

Failed variants must remain in the experiment ledger.

No best-of-N result may be presented as if N=1.

Multiplicity control must be frozen before substantive evaluation.

---

# 24. Ablation policy

Ablations should change one meaningful component at a time where possible.

Current conceptual ordering remains:

baseline
-> Regime
-> Regime + OI
-> Regime + Positioning
-> Regime + Taker

and separately:

Event + Price
vs
Event + Price + Mechanics

These comparisons remain BLOCKED until their required causal evidence gates
pass.

No blocked Mechanics hypothesis becomes testable merely because economic
accounting exists.

---

# 25. Failure conditions

A run is scientifically invalid or non-promotable if any required condition
fails, including:

- population not frozen before outcomes;
- future information leakage;
- causal availability violation;
- missing required provenance;
- holdout contamination;
- undocumented protocol deviation;
- post-hoc threshold change;
- hidden variant search;
- mandatory cost silently substituted with zero;
- inconsistent trade lineage;
- inability to reproduce manifest identity;
- unregistered change to risk or sizing.

Invalid experiments are preserved as failures.

They are not repaired retrospectively into passing evidence.

---

# 26. Stop conditions

Stop evaluation and classify the run before proceeding when:

- evidence integrity fails;
- provenance chain breaks;
- protocol version differs from manifest;
- required timestamps become non-causal;
- population membership changes after outcome access;
- confirmation evidence is accidentally exposed;
- implementation bug changes economic semantics;
- required mandatory cost completeness falls below the frozen eligibility rule.

A stopped experiment may be redesigned under a new protocol version.

Its prior outcomes must not be reused as pristine unseen confirmation.

---

# 27. Promotion requirements

Passing P0 economic evaluation does not establish validated Edge.

At minimum, future promotion would require:

- sufficient sample;
- preserved protocol;
- OOS/discovery survival;
- cost sensitivity;
- temporal stability;
- regime coverage;
- multiplicity control;
- prospective PAPER evidence;
- independent confirmation.

Real capital remains unauthorized by this protocol.

---

# 28. Explicit non-claims

This protocol does not claim:

- profitable trading;
- positive expectancy;
- acceptable drawdown;
- validated Regime;
- validated Mechanics;
- validated Alpha;
- policy superiority;
- live execution quality;
- Knowledge validation;
- Criterion improvement.

Scientific status remains:

EDGE=NOT_DEMONSTRATED
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE

---

# 29. Parameter authority resolution

This section resolves the open protocol-authority questions identified during
the pre-registration audit.

## 29.1 Risk and sizing authority

CP-8 does not define a new universal numeric risk percentage.

Economic accounting inherits the exact frozen upstream risk and allocation
authority that produced the decision.

Required lineage includes the applicable:

- RiskPolicy;
- AllocationPolicy;
- risk budget;
- authorized allocation;
- policy identities;
- registration timestamps.

Accounting consumes authorized size.

Accounting must not choose, optimize, rescale or retrospectively normalize
position size.

Therefore the P0 economic baseline does not require a new global numeric risk
parameter.

Any later experiment that compares alternative risk policies must register
those alternatives as separate experimental variants before outcome access.

## 29.2 Primary drawdown convention

For CP-8 P0:

PRIMARY_DRAWDOWN=CLOSED_EQUITY_DRAWDOWN

Closed-equity drawdown is the primary supported drawdown metric because the
repository already contains an explicit closed-equity convention.

It must not be represented as intratrade or mark-to-market drawdown.

MARK_TO_MARKET_DRAWDOWN=NOT_SUPPORTED_YET

A future mark-to-market metric requires its own causal valuation contract and
must not silently replace the P0 convention.

## 29.3 Primary reference comparator

The primary P0 synthetic comparator is the existing repository reference rule:

REFERENCE_RULE_ID=pnep-synthetic-vote-sum
REFERENCE_RULE_VERSION=1

This reference rule is a synthetic control.

It is not calibrated Alpha, validated Alpha, a policy winner, or evidence of
economic Edge.

Additional reference policies require separate pre-registration before their
results are inspected.

ReferenceForecasts are not automatically part of P0 merely because the
infrastructure exists.

## 29.4 Sample sufficiency boundary

CP-8 P0 is an economic measurement baseline, not an Edge-promotion test.

No universal numeric minimum sample is introduced here.

Historical thresholds such as n>=30, n>=50 or 100 records belong to their
specific prior protocols and are not promoted into a universal P0 rule.

Until an economic qualification protocol is separately pre-registered:

SAMPLE_SUFFICIENT=NO

P0 observations may accumulate and descriptive metrics may be computed, but
sample accumulation alone cannot promote Edge.

The later economic qualification protocol must freeze sample requirements from
its estimand, expected effect size, variance, temporal dependence, regime
coverage, cost uncertainty and tested family before confirmatory outcome
access.

## 29.5 Multiplicity boundary

CP-8 P0 does not select a winning policy and does not perform best-of-N search.

Therefore no multiplicity correction is required merely to record descriptive
P0 economics.

Any later inferential comparison across policies, thresholds, horizons,
regimes, Mechanics variables or other variants must pre-register the full
family and an appropriate dependence-aware simultaneous inference method.

Existing calendar-time block-bootstrap infrastructure may be reused only where
its statistical unit and assumptions match the registered experiment.

Earlier experiment-specific block sizes, resample counts and minimum-N values
are not automatically inherited by P0.

POLICY_WINNER=NONE

## 29.6 Cost completeness boundary

For P0, entry and exit prices already come from the executable side of the
causal simulated PAPER book:

- BUY entry uses ASK;
- SELL entry uses BID;
- SELL exit uses BID;
- BUY exit uses ASK.

Therefore observed bid/ask spread is already embodied in simulated execution
prices and must not be added again as a second spread charge.

Factual venue slippage remains:

observed_slippage = UNKNOWN

A configured slippage model may exist only as separately labelled scenario
analysis.

Fees require causal applicable fee evidence.

Without that evidence:

fee_cashflow = UNKNOWN

Funding rate is not funding cashflow.

Funding cashflow requires causal proof that the simulated position was exposed
to an applicable funding event plus the required rate, timing, notional/basis,
direction and provenance.

The exact funding applicability test depends on the authoritative modern PAPER
open/close timestamps and is therefore deferred until CP-7L is published and
audited.

Until mandatory applicable costs are resolved:

net_pnl = UNKNOWN
net_return = UNKNOWN

Gross economics remain separately reportable when their own lineage is
complete.

No UNKNOWN cost may be converted to zero.

---

# 30. CP-8 scope boundary after authority resolution

CP-8 is responsible for:

PaperClosedPosition
-> gross economic measurement
-> explicit cost assessment
-> fail-closed net economic measurement

CP-8 is not responsible for:

- Edge promotion;
- policy winner selection;
- Mechanics validation;
- Regime validation;
- confirmation holdout access;
- Knowledge validation;
- Criterion updates;
- live capital authorization.

Those remain later scientific checkpoints.

Current scientific state remains:

EDGE=NOT_DEMONSTRATED
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE
SAMPLE_SUFFICIENT=NO

The only remaining execution-contract dependency for final CP-8 accounting
implementation is the authoritative CP-7L closed-position boundary.