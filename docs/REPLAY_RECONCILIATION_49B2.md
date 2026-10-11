# 49B.2 Replay Reconciliation Certificate

The public reconcile_causal_replay API runs the existing causal replay twice
against the same ledger/instrument/cutoff/feature contract, using separate fresh
private temporary graph stores. It compares all serialized certificate fields,
including identities, ordered lineage, missing/unknown/unconsumed fields and
subgraph hash. Differences are preserved, never sorted away within certificates.
A feature iterator is consumed once. No current ledger-head or filesystem path
enters reconciliation identity; valid later evidence preserves historical identity.

The immutable result serializes both commitments and exact different_fields.
status is MATCH or MISMATCH; require_match raises on MISMATCH. Exceptions fail
closed without producing a certificate. The result constructor is a representation,
not proof of execution: consumers must use the public reconciliation function.
Both runs use the same algorithm; common-mode errors remain possible. MATCH is
not provider truth, causal identification, prediction quality or Edge.

Source ledgers are read-only. Graph materializations are temporary and discarded.
No retries, network, backfill, outcomes, learning or LIVE promotion. Concurrent
ledger changes relevant to the cutoff may mismatch/fail; no retry masks them.

Preflight 2026-10-11 16:29 UTC: Metrics 11 SUCCESS / 4 FAILED / 0 INVALID,
current 0, longest 8. Slot 16:00 failed correctly because taker ended at 15:55
while four other components included 16:00. No repair/retry; runtime still running.

Next bounded checkpoint: an explicit read-only reconciliation CLI with create-only
certificate export for reproducible operator invocation. Do not begin regime or
mechanics research until their causal prerequisites are independently established.

Qualification found SQLite transaction contexts did not close graph connections.
The store now explicitly closes all three connections while preserving transaction
commit/rollback. Windows temporary-graph cleanup is covered by reconciliation tests.
Focal boundaries: 35 passed. Compile and diff check: PASS.

Full DEV pytest: 2331 passed, 5 skipped, 3 existing fixture warnings (468.50s).
