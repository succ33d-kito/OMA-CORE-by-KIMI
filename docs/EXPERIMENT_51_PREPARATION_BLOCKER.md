# Experiment 51 preparation — protocol ambiguity (51-PRE)

Status: HORIZON_BLOCKER_RESOLVED on 2026-10-13; historical stop record. This is a blocker record, not a frozen
experiment or evidence of predictive value.

Baseline: ff91dd629997ffc9ad386dfbf65b4c5fad6ede5e.
Branch: manual/51-pre-readiness-prereg-20261012.

## Primary horizon requires an explicit research decision

The requested Experiment 51 compares Event + Price against additions of Regime,
supported Mechanics, and both on identical eligible opportunities. No primary
numeric horizon for that comparison was found in the inspected contracts.

* research/metrics_2024_2025/PROSPECTIVE_H1_PREREGISTRATION.json freezes 4 hours
  for a different hypothesis: rising OI plus taker ratio > 1 within Regime range
  versus other eligible range observations. Its five-horizon family, 90-day gate,
  minimum sample, and research cost hurdle belong to that study. They do not
  establish a frozen P0/PR/PM/PRM protocol.
* docs/OMA-PNEP-1.0-POLICY-KERNEL-v1.md requires an explicit positive horizon
  and economic specification commitments; it supplies no economic defaults.
* research/work_pc_preparation/CP8_P0_ECONOMIC_BASELINE_PROTOCOL.md, section 6,
  explicitly freezes no universal numeric horizon: the lifecycle is thesis-driven.
* research/edge_discovery/mechanics_v2_1/FREEZE.json and the MM registry retain
  null primary horizons; they cannot supply the missing decision.

The 51-PRE request requires stopping if the primary horizon is genuinely
undefined. Do not silently import 4h, a synthetic fixture horizon, or a lifecycle
horizon. Required next decision: explicitly authorize one primary horizon and its
scope for the Experiment 51 paired comparison. Any adoption from the OI/taker
study is a NEW registration decision, not evidence of a pre-existing freeze.

## Dependency findings already established from code

role_price_window requires exactly 81 ordered contiguous raw BTCUSDT H1 prices,
causal availability, contemporaneous capture and verified role attestations.
causal_regime rebuilds this certificate; Metrics and Funding are not dependencies
of this Regime contract.

causal_mechanics projects available authenticated raw snapshot inputs and retains
missing features. Regime is optional. It does not require every snapshot feature
as a universal readiness gate. Unsupported dimensions, including OI change,
aggressor flow and realized funding payment, remain unknown. A chosen Mechanics
experimental subset must therefore be frozen before declaring experiment readiness.

common_support authenticates per-opportunity policy eligibility and shared
controls. An H1 intersection of collectors alone cannot establish this eligible
Event/decision population or authorize the experiment.

## Scope at stop

No readiness implementation, experiment preregistration or harness was created.
No primary metric, MES, cost model or new split was frozen. No outcome analysis,
real experiment, holdout access or policy selection was performed. No source,
collector, runtime, prospective state, LIVE checkout or security setting was changed.
No new tests were necessary for this documentation-only blocker; hybrid validation
and publication of implementation remain pending. This record is left uncommitted.

REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE
EDGE=NOT_DEMONSTRATED
REAL_CAPITAL_AUTHORIZED=NO

## Resolution
Project owner explicitly selected NEW ex-ante 4H primary and 1H/8H secondary horizons. Incorporated into EXPERIMENT_51_PREREGISTRATION.json and .md. The horizon blocker is closed; executable rule/population/activation bindings remain separate prerequisites. The earlier scope-at-stop section is historical.
