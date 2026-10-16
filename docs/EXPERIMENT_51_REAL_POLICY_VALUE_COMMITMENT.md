# Experiment 51 — real policy value adapter and policy-blind decision rule commitment

Status: **QUALIFIED (ex-ante commitment artifact added; no outcome inspected)**
Date: 2026-10-16
Branch: `manual/51-real-policy-value-rule-20261016`
Baseline: `15b685729522a3090d05078a4049521ecd9b650b`
Canonical preregistration (unchanged): `7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8`

## 1. What was already frozen before this cut

The preregistration's `rule_boundary` requires that *"Actual causal value adapter and identical
policy-blind decision rule/thresholds must be separately frozen before ANY prospective outcome
inspection"*. Reading the code (not chat history) shows those semantics were already implemented and
committed **ex ante**, in the same lineage:

| Element | Artifact | Commitment |
|---|---|---|
| P0 real value/action | `experiment51_p0._agreement` | `P0_HASH = d6c448957b69e5b469ac1672d54d8516e2b3a8e420b8b3434a3422f002b3a70d` |
| PR / PM / PRM derivation | `experiment51_derived.actions`, `RULES` | `7e424abf…`, `543a8bba…`, `72c1b976…` |
| Rule family binding | `FAMILY` | `fb544840ed74099134f082e537c76fbbd84b09e7cdaeb10ae919c40b7afeffdd` |
| Event direction input | `event_direction_v1.RULE_HASH` | `6a07b7e1d5a1ed2f9a9635de362b50844d5c9092bea52792f3391da3e9045833` |
| Sealing of rules into a phase | `experiment51_sealed.activate_phase/_phase/_gates` | seals `prereg=PREREG, rules=list(RULES), family=FAMILY, controls_id` |

Semantics (all categorical, no numbers chosen from data):

* P0 = **equal LONG/SHORT only, otherwise ABSTAIN** (Event direction ∧ Price H1 direction).
* PR = P0 with **Regime veto**: pass on `trend`/`range`, abstain on `transition`/`unknown`/missing.
* PM = P0 with **Taker confirm**: LONG requires `taker > 1`, SHORT requires `taker < 1`, `= 1` abstains.
* PRM = both; derived actions **never create or reverse** a P0 action.
* ABSTAIN utility is zero and cost is zero; UNKNOWN is not zero and missing is not neutral.

## 2. What this cut adds (additive only)

`core/scientific/policy_value_commitment.py` — an **outcome-blind** commitment artifact in the
existing frozen-binding pattern. It does not redefine semantics, does not touch the prereg JSON and
performs no I/O. It:

1. binds the adapter, the single policy-blind rule and the threshold specification to the canonical
   preregistration commitment;
2. restates the thresholds **independently** (`expected_actions`) and verifies them exhaustively
   against the executable implementation (`derived.actions`) over the whole frozen domain
   (3 actions × 5 structures × 4 taker values = 60 combinations), so the implementation cannot
   silently diverge from what is committed;
3. re-checks that `families()` matches the prereg `information_sets` (`P0=EVENT,PRICE`,
   `PR=+REGIME`, `PM=+MECHANICS`, `PRM=all`), that `RULES[0] == P0_HASH`, that `FAMILY` recomputes,
   and that the prereg document still canonicalises to the frozen hash.

Committed identifiers:

```
REAL_POLICY_VALUE_ADAPTER_ID    = experiment51-real-policy-value-adapter-v1
REAL_POLICY_VALUE_ADAPTER_HASH  = 668949b255f3fb17ef24e2285418cb3faa487d24a8417797c6af68e425acc963
POLICY_BLIND_DECISION_RULE_ID   = experiment51-policy-blind-decision-rule-v1
POLICY_BLIND_DECISION_RULE_HASH = 9ec6691ca07f44e454ac96502aa4028e57b77d174970b8cc3390780954738276
THRESHOLD_COMMITMENT_HASH       = 14a0d8281cd4b21e9669c7658b7f425e9eee35b50f4c83b9652a2d89f4e9f2f0
BUNDLE_COMMITMENT               = 04be79661eb07afb891227c18c411f2b54a9da32bbf70494552281f308fd0ce0
```

`THRESHOLDS_SOURCE = already-frozen P0_HASH / RULES semantics` — no threshold was chosen, estimated,
optimised or tuned here, and no outcome-derived quantity exists anywhere in the path.

## 3. Outcome contamination

Audited statically and by test over the decision path
(`policy_value_commitment`, `experiment51_p0`, `experiment51_derived`, `decision_rule`,
`policy_kernel`): **no import of `experiment51_sealed`** and no identifier mentioning
label/return/pnl/realized/forward semantics. The only accepted occurrence of "outcome" is
`controls.outcome_horizon_seconds` — the frozen 14400 s (4H) causal control parameter — plus the
audit flag `outcome_dependency=False`. Outcome access lives exclusively behind
`experiment51_sealed._load_labels` and its private permit, after the explicit firewall comment
("no loader call exists above this line").

## 4. Qualification

| Suite | Result |
|---|---|
| `tests/test_policy_value_commitment.py` (new) | **22 passed** |
| `tests/test_decision_rule.py` | 21 passed |
| `tests/test_policy_kernel.py` | 32 passed |
| `tests/test_experiment51_derived.py` + `test_experiment51_sealed.py` + `test_common_support.py` | 114 passed |
| `git diff --check` | clean |

The new suite covers the 20 required properties (determinism, no outcome field, no future-evidence
entry point, fail-closed abstention, UNKNOWN≠0, missing≠neutral, no probability relabelling, one
shared rule, arm identity cannot change thresholds, provenance, deterministic adapter/rule/threshold
hashes, LONG/SHORT/ABSTAIN boundary behaviour, deterministic ties, malformed input rejection,
policy-blind invariant, no label/outcome dependency) plus regression checks that the synthetic
`ReferenceRule` remains isolated and non-executable, that the prereg artifact is unmodified, and that
the commitment matches what the sealed phase binds.

## 5. Relationship to the prereg blocker

The prereg JSON still lists `REAL_POLICY_VALUE_RULE_NOT_QUALIFIED` in `execution_blockers`. That
artifact is historical and is **not modified** by this cut. The blocker is now materially covered:
a real causal value adapter exists, one identical policy-blind rule serves all four arms, thresholds
are fixed ex ante by committed semantics, and all of it is bound to the canonical prereg commitment
by the artifact above. Removing the entry from the prereg would require a separate prereg revision.

## 6. Explicit non-actions

No outcome/label inspection, no Experiment 51 execution, no phase activation (DISCOVERY or
CONFIRMATION), no Kraken access, no EventDirection creation, no P0, no event-population binding,
no Regime/Mechanics semantic change, no Price/Metrics/SEC modification, no historical gap repair,
no `main` merge. `PROSPECTIVE_OUTCOMES_INSPECTED=NO`.
