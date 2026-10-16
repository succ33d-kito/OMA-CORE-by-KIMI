# 50A + 50B checkpoint — 2026-10-11

Branch: `manual/50ab-causal-regime-mechanics-20261011`.
Base: `85a8ac2ed38f266ad05340853b281be12537244e`.
DEV only: `<OMA_CORE_DEV>`.

## Recovery and completed implementation
The interrupted earlier work stopped during inspection after `0f24bbf`; subsequent
manual commits already closed price/funding role authentication and 49A/49B.
This branch builds on that closed baseline rather than repeating it.

- `325d68a`: exact role-authenticated 81H certificate and persisted Regime v2.
- `f497959`: causal descriptive Mechanics, explicit null unsupported dimensions.
- `1c29725`: exact derived graph lineage and independent replay reconciliation.
- This documentation-only commit records qualification; no source changed after tests.

## Files
Added modules: `core/scientific/role_price_window.py`, `causal_regime.py`,
`causal_mechanics.py`, `derived_causal_replay.py`.
Added tests: `tests/test_role_price_window.py`, `test_causal_regime.py`,
`test_causal_mechanics.py`, `test_derived_causal_replay.py`.
Added contracts: `docs/50A_CAUSAL_REGIME_INTEGRATION.md`,
`50B_CAUSAL_MARKET_MECHANICS_INTEGRATION.md`, `DERIVED_CAUSAL_REPLAY.md` and this file.
Modified existing source: one additive relation in `core/intelligence_graph/store.py`.

## Qualification
Focal regression selection: **71 passed**.
Full DEV suite: **2388 passed, 5 skipped, 3 warnings in 700.31s**.
Command: Python -m pytest -q -p no:cacheprovider --basetemp <unique external temporary directory> --tb=short.
Python: existing OMA-CORE .venv; PYTHONDONTWRITEBYTECODE=1.
Five implementation modules compile successfully; git diff --check PASS.
The supplied baseline reported 2381 passed/4 skipped; this run added eight test
functions but observed one additional skip. No cause is inferred from the count.
Three warnings concern existing paper-trading class-scoped pytest fixtures.

Adversarial checks exposed and fixed JSON tuple/list reconstruction inconsistency
and the incompatibility of generic raw availability with specialized Metrics gates.
Mechanics now rebuilds the authenticated raw snapshot and its exact availability
contract, preserving the frozen generic gate. Forged/relabelled derived envelopes
are compared with exact persisted rows and reconstructed inputs.

All five frozen surfaces have zero diff against baseline. LIVE tracked tree remains
clean at `d9e0f72ec0e1eb897a240a6ecd5820403de039e5`; this mission writes only DEV.
No live capture, deployment, historical rewriting, holdout experiment or tuning.

## Status and remaining limits
49A=COMPLETE; 49B=COMPLETE (preserved).
50A_CAUSAL_REGIME_INTEGRATION=COMPLETE (infrastructure).
50B_CAUSAL_MARKET_MECHANICS_INTEGRATION=COMPLETE (supported descriptive subset).
REGIME_IMPLEMENTED=YES; REGIME_CAUSALLY_INTEGRATED=YES; REGIME_VALIDATED=NO.
MECHANICS_IMPLEMENTED=YES; MECHANICS_CAUSALLY_INTEGRATED=YES; MECHANICS_VALIDATED=NO.
POLICY_WINNER=NONE; EDGE=NOT_DEMONSTRATED; REAL_CAPITAL_AUTHORIZED=NO.

Absent/unsupported inputs stay UNKNOWN. No participant intent, absorption,
OI change, aggressor flow, trade intensity or funding payment is inferred.
Historical Mechanics v2.1/MM hypothesis blocks remain intact. These tests prove
infrastructure behavior using synthetic qualified fixtures, not real 81H coverage
or predictive value. New branch publication does not deploy into LIVE or merge main.
Next boundary: separately qualify real role-authenticated inputs before authorizing
any frozen comparative experiment; do not unblock hypotheses from infrastructure alone.
