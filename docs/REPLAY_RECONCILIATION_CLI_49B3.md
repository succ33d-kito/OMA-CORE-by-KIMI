# 49B.3 — operator reconciliation export

Run with the qualified Python:

    python scripts/reconcile_causal_replay.py --ledger <existing scientific.db> --instrument BTCUSDT --as-of <aware ISO cutoff> --output <new certificate.json>

Optional repeated --feature fixes an explicit feature contract. No implicit current
cutoff, ledger creation, source repair or network. Two independent temporary graphs
are produced by 49B.2. Output creation is exclusive; existing output is never replaced.
MATCH exits 0. MISMATCH exports exact diagnostic certificate and exits 2. Exceptions
propagate without a certificate if reconstruction fails. A crash during export may
leave partial JSON; never interpret an incomplete file as a valid certificate.
The output is not signed or a durable deployment qualification record.

Tests use temporary synthetic ledgers. No real scientific ledger was replayed here,
no LIVE promotion, no Edge claim. The complete 49B.2 suite ran before this CLI-only
checkpoint; qualification here covers CLI and direct replay/graph boundaries.

Next priority: audit the boundary between admitted Metrics rows and causal fabric
before adding derived Regime/Mechanics. Preserve the dedicated atomic admission
contract and prove that partial or inconsistent bundle membership cannot enter
causal snapshots. No model optimization or retrospective repair.

Qualification: 34 focal/direct-boundary tests passed; compile and diff check PASS.
