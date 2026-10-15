# OMA-CORE + StarNet — authoritative roadmap vNext

Updated 2026-10-15. Owner-specified target architecture; documentation only.
Scientific baseline: 46c1f0986bdb5f02bc95fa428defda83b2f4f390.
This document supersedes June-era current-state descriptions without erasing history.

## Authority and status vocabulary

REALITY -> OMA (observe -> reconstruct -> hypothesize -> falsify -> know)
-> Criterion -> resource/decision allocation -> StarNet action
-> Outcome + Accounting + Attribution -> evidence-gated Knowledge -> OMA.
OMA is the epistemic/scientific authority; StarNet is the operational/economic network.
StarNet may explore and act but cannot create scientific truth from successful outcomes.
Incomplete provenance => NO LEARNING. Unvalidated Knowledge => NO Criterion update.
Outcome != LearningSignal. Criterion must not learn directly from PnL.

Track separately: IMPLEMENTED, OPERATIONAL, CAUSALLY AVAILABLE,
SCIENTIFICALLY VALIDATED, ECONOMICALLY VALIDATED, BLOCKED, FUTURE. Never use DONE
as a substitute for these independent dimensions. Unassessed does not mean PASS.

## Current evidence (dated UTC; no general repository audit)

Read-only refresh 2026-10-15 18:10 UTC:
- Price: 53 valid H1, current streak 1, longest 48, latest slot 18:00 UTC;
  integrity PASS, 81H gate NO. Gap beginning 2026-10-14 19:00 UTC stays permanent.
- Metrics capture: 84 valid, current streak 0, longest 12; 13 post-authority valid.
  Exactly one authenticated atomic admission, slot 2026-10-15 00:00 UTC, one Taker
  input. MECHANICS_REAL_PATH_OBSERVED=YES; Metrics/Mechanics readiness NO.
  Publication: 3204f5b8805a864d28cba12ed24645f6a91a4eceeb7ad48b9d6681d705ef275e.
- SEC latest verified prior snapshot: one prospective discovery; zero full receipts,
  admissions, direction attestations and P0 eligible opportunities. Recent scheduled
  runs fail before HTTP opening poll.lock. Historical HTTP_FAILURE does not identify
  403/429/503. First_seen and original failures must remain immutable.
- Metrics scheduled runs fail INSERT START in attempts.sqlite with readonly error.
  Existing admitted evidence still authenticates. Nominal ACLs match Price; exact
  OS cause requires file-I/O tracing. No remediation is authorized by this document.
- Funding capture/role contracts exist; fresh Funding health not qualified here.
  Funding is not a primary Experiment 51 dependency.
- Causal fabric/replay, Regime/Mechanics, policy kernel, common support, manifests,
  official binding, Event direction/P0 and PR/PM/PRM machinery are implemented with
  recorded qualification. This does not validate predictive or economic value.

DISCOVERY_ACTIVATED=NO; EXPERIMENT_51_READY=FALSE; EXPERIMENT_51_EXECUTED=NO;
REGIME_VALIDATED=NO; MECHANICS_VALIDATED=NO; POLICY_WINNER=NONE;
EDGE=NOT_DEMONSTRATED; REAL_CAPITAL_AUTHORIZED=NO.
No revenue/self-funding/economic-loop completion is established by this cut.

## Track 0 — governance and integration debt

Remote main and merge-base: d84a383463242b24a502edfeab6a440b26bd406d.
Scientific HEAD: 46c1f0986bdb5f02bc95fa428defda83b2f4f390.
Verified main-only=0; scientific-only=37 commits. Documentation commits add to the
branch delta; they do not synchronize main. MAIN_GOVERNANCE_RESOLVED=NO.
Absent work covers 49A fabric/replay, 50AB causal Regime/Mechanics, role Price and
retry runtime, 51 preregistration, Event direction/activation/discovery, derived
policy bindings, durable Metrics publication and prospective admission.
Active remote scientific branches absent from main:
- manual/49a-causal-observation-fabric-20261011
- manual/50ab-causal-regime-mechanics-20261011
- manual/51-price-role-runtime-20261012
- manual/51r2-price-explicit-retry-20261012
- manual/51-pre-readiness-prereg-20261012
- manual/51-event-direction-v1-20261013
- manual/51-event-activation-20261013
- manual/51-derived-policies-bindings-20261013
- manual/51-real-event-path-20261013
- manual/51-metrics-real-admission-20261014

GOV-0.1 synchronize memory; GOV-0.2 controlled main integration policy;
GOV-0.3 retain one dated current-state authority (this document).
Future integration: inspect exact ancestry/diff, reconcile qualification against
selected tip, review controlled integration, obtain applicable owner authorization.
No merge/rebase/reset/force push here. Runtime promotion is separately qualified.
Preserve historical snapshots; refresh evidence dates at each material checkpoint.

## Track A — scientific core

A1: real causal Price, Metrics, Event, Funding where required, role-aware PIT
observations and common support. Exit: CAUSAL_REALITY_READY independently verified.
A2: past-only Regime and supported Mechanics with exact provenance/replay;
implemented or observable != validated. Missing inputs stay UNKNOWN/ineligible.
A3: frozen P0/PR/PM/PRM, identical CS4, MES, costs, temporal bootstrap,
multiplicity, separately authorized DISCOVERY/CONFIRMATION/OOS, sealed holdout.
See [preregistration](EXPERIMENT_51_PREREGISTRATION.md) and
[derived bindings](EXPERIMENT_51_DERIVED_POLICIES.md). Later adapters supersede
obsolete preparation-stage missing-code descriptions; runtime gates remain binding.
Primary 4H is an ex-ante owner decision, not automatically inherited; secondary
1H/8H cannot rescue it. Frozen preparation: 168H calendar blocks, 2000 paired
resamples, seed 51, Bonferroni across three primary comparisons, 2bps practical
hurdle after 10bps research round-trip cost. Exact JSON remains authoritative:
7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8.
No retuning from results; PILOT never relabelled DISCOVERY. Binance 2024 discovery;
previously exposed Binance 2025 secondary temporal confirmation, not pristine.
Kraken XBTUSD Spot Q2-2026 remains SEALED_CROSS_EXCHANGE_HOLDOUT.
Valid verdicts: EDGE_DEMONSTRATED, EDGE_NOT_DEMONSTRATED, INCONCLUSIVE.
A4 optional hypothesis factory: Expectations, Positioning, OI, Funding, Flow,
Cross-Asset, Market Sensitivity, Kronos, Qlib, RD-Agent, FinGPT, Chronos.
Register every experiment to expose multiple testing; candidates do not judge truth.

## Track B — execution and capital

B1 PaperClosedPosition -> Accounting -> Outcome -> Attribution -> evidence-gated
Knowledge, with reconciliation and complete provenance before closure.
B2 qualify orders/precision, fills, fees, spread, slippage, funding, position
reconciliation, failure recovery, kill switch and capital limits.
B3 pre-edge microcapital ONLY for bounded execution learning with EXECUTION_READY,
RISK_READY, ACCOUNTING_READY, CAPITAL_LIMITS and explicit OWNER_AUTHORIZATION.
B4 adapt allocation to real CapitalState, never assumed starting capital.
EDGE != LIVE CAPITAL; EDGE != PnL; LIVE CAPITAL != EDGE;
POSITIVE PnL != DEMONSTRATED EDGE; EXTERNAL REVENUE != TRADING EDGE;
EXECUTION READINESS != EDGE.

## Track C — accounting and resource intelligence (target)

C1 deterministic double-entry ledger, receipts, classification, reconciliation,
audit trail. C2 Finance/Accounting Star interprets; deterministic software books
and reconciles. The agent is NOT the ledger. Reporting targets: P&L, Balance Sheet,
Cash Flow, Budget vs Actual, Experiment P&L, department contribution, ROI, ROIC,
Contribution Margin, Burn, Runway and Capital Utilization.
C3 CapitalState: cash, reserves, receivables/payables, revenue, fixed/variable costs,
free cash flow and risk/experiment/trading capital. Resources: time, compute,
attention, audience, distribution, data, IP, reputation.
C4 Criterion eventually compares marginal dollar/hour/compute/experiment across
Trading, Affiliate, Services, Content, Research, Infrastructure and Cash.

## Track D — StarNet (future)

D1 Protocol v0: Star, Capability, Permission, Budget, Action, Receipt, Outcome,
Escalation, HumanApproval. D2 Affiliate low-capital scalable engine;
D3 Services/Automation may reach first cash earlier; D4 Content/Media builds
attention/distribution/audience/trust; D5 LeadGen, digital products, SaaS,
research intelligence, procurement, investing after evidence and authorization.
Milestones: first external revenue, first $1, first $20 contribution, monthly
operating cost covered. None establishes trading Edge.

## Track E — open-source capability layer (future)

Registry: name/version/source/license/domain/function, cash/API/compute/integration/
maintenance costs, quality/reliability/latency/coverage, PIT compatibility,
provenance/reproducibility/replaceability and authority level.
States: DISCOVERED, AUDITED, SANDBOX, QUALIFIED, ACTIVE, REJECTED.
A commodity examples: Pydantic, Pandera, DuckDB, Alembic, APScheduler,
pytest-xdist, Tenacity. B adapted examples: Fincept, OpenBB, public-apis, Kronos,
Qlib, RD-Agent, NautilusTrader, hftbacktest, Graphiti, Jev; wrap behind interfaces,
never grant epistemic authority. C OMA/StarNet core: causal evidence, Criterion,
Decision Approval, Outcome-to-Knowledge, reverse/counterfactual reasoning,
resource allocation, protocol and scientific validation.
FREE SOFTWARE != ZERO ECONOMIC COST. Compare engineering/integration/maintenance,
compute, dependency/security/license risk and opportunity cost. These are owner
candidate lists, not audited product/license recommendations.

## Capital principle

CAPITAL-AGNOSTIC / RESOURCE-AWARE: $0, $10, $100, $500, $1,000 or larger actual
budgets. No module assumes deployable capital except where intrinsic to an
explicitly authorized action. At $0, time, skills, knowledge, compute, data,
distribution and IP can be transformed into value/cash flow.

## Gates and closure evidence

| Gate | Required closure | Current state |
|---|---|---|
| G0 | Repository/memory/roadmap aligned | Synchronized by this documentation |
| G1 | Required causal real inputs and common support | BLOCKED |
| G2 | Frozen Experiment 51 gates and bindings | BLOCKED |
| G3 | Auditable registered primary verdict | NOT EXECUTED |
| G4 | Economic accounting/outcome/attribution/learning loop | NOT ESTABLISHED |
| G5 | Reproducible OMA v1 acceptance including recovery | NOT ESTABLISHED |
| G6 | Qualified StarNet Protocol v0 | FUTURE |
| G7 | Auditable first external revenue | NOT ESTABLISHED |
| G8 | Monthly operating costs covered | NOT ESTABLISHED |
| G9 | Execution/risk/accounting/limits + owner authorization | NOT AUTHORIZED |
| G10 | Reconciled positive retained earnings | NOT ESTABLISHED |
| G11 | Governed multi-Star resource allocation | FUTURE |
| G12 | Auditable OMA/StarNet self-funding | FUTURE |

Nonlinear: G7 may precede G3; G9 may precede G3 only for bounded execution learning.
Neither implies Edge. Documentation synchronization does not close main debt.

## Current priority / next checkpoints

1. Exact SEC/Metrics file-I/O diagnosis; no remediation in this cut.
2. Preserve prospective Price and genuine gaps.
3. Synchronize roadmap/memory/governance.
4. Separately authorize minimum proven operational repair.
5. Reach common causal readiness.
6. Execute Experiment 51 only under frozen prerequisites.
7. Close economic Outcome/Accounting/Knowledge; OMA v1 acceptance.
8. StarNet v0; zero/low-capital economic deployments; expand on evidence.

Track I tracing and Track II documentation are independent. Incomplete tracing
does not block docs; docs publication does not authorize remediation or deployment.
