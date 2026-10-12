# Experiment 51 synthetic harness boundary

`experiment51_preparation.synthetic_smoke()` accepts no dataset argument. It
manufactures deterministic toy labels/actions, applies the frozen active research
cost and paired three-arm differences, then performs the preregistered calendar
block bootstrap. Its immutable receipt always says SYNTHETIC_ONLY, no real
experiment, no winner and no scientific verdict. Synthetic utility is not market
PnL. Zero bootstrap variance gives an undefined interval, never a pass.

`bind_support` reuses the actual CommonSupportRegistry, commits exclusions as
well as eligible IDs and rejects mixed roles. `_paired` rejects arm-specific
population deletion. Snapshot reconstruction/causality and shared controls remain
upstream existing contracts tested in the related suite, not new duplicate models.

This is intentionally not a live experiment runner. It does not load real outcomes,
join collector databases, materialize derived observations, bind activation dates
or adapt real features into actions. No fixture may be promoted to real evidence.
Those exact missing bindings are reported as readiness blockers. Primary/secondary
label construction and phase-boundary purging are frozen definitions, not a claim
that a real label loader has been implemented or tested. No real execution entry
point exists until those remaining components are separately qualified.

Hybrid validation: focal/related and explicit Windows-only partition locally;
full Linux collection runs offline using the prior exact-node Windows partition.
The new Metrics activation fixture has one explicit Linux skip and must pass
Windows. Existing 12 OHLCV-dependent paper tests retain their original skips.
The CI workflow is branch-scoped to the requested DEV branch; no main merge or
runtime deployment. Reproduced dependency pins are from the already qualified
51-R2.1 environment and public PyPI only. Local controls stay enabled.
