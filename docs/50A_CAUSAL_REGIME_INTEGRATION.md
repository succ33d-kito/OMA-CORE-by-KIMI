# 50A causal Regime integration

Additive infrastructure from baseline `85a8ac2ed38f266ad05340853b281be12537244e`.

## Reuse and boundaries
The old price certificate and Regime observation remain unchanged. New
`role_price_window.certify_role_price_window` requires exactly 81 explicit ordered
BTCUSDT H1 receipt IDs, an explicit role and an aware cutoff. It authenticates
all 81 raw prices and all 81 role attestations through existing gates. Duplicate,
conflicting, missing, noncontemporaneous or unavailable dependencies fail closed.
Its identity commits ordered prices, exact attestations, role and cutoff; it does
not commit the current ledger head, preserving historical reconstruction.
Authority claim: **authorization strictly precedes earliest persisted capture evidence**.
This does not prove a stronger pre-network-request authorization claim.

`causal_regime.append_causal_regime` rebuilds the certificate, reuses MarketState
`ohlcv-v1` and `classify_regime` method `er20-vol20-vs-prior60-v1` unchanged, and
persists `Regime/Role/v2` with all 162 dependencies. Computation cannot precede
the input cutoff. Actual derived availability comes from the existing ledger
writer; historical inputs do not imply historical computation availability.
Consumers reconstruct the certificate and calculation and match the exact
persisted row. Replay is idempotent and cannot relabel a supplied object.

Status is `DESCRIPTIVE_HEURISTIC_NOT_PROBABILITY`. Raw 49A snapshots continue to
exclude derived rows. No classifier calibration, outcomes or holdouts are used.
See DERIVED_CAUSAL_REPLAY.md for graph/reconciliation contract.
