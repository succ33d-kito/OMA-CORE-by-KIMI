# Metrics admission chronology correction â€” qualification checkpoint

Baseline: b99c788173fda685dcf98eb44142c81305bd4085.
Branch: manual/51-metrics-real-admission-20261014.
Status: implementation and local qualification complete; full isolated CI PENDING.
No real admission authority is activated by this change.

## Reproduction
The new regression failed on the original implementation: row clocks 13:04,
final validation delayed until 14:00:01, decision 14:00 accepted all six rows.
It now requires rejection. Synthetic clocks and temporary ledgers only.

## Additive contract
Admission v2 preserves observation identity construction and six-row atomicity.
Source and final verification precede a SQLite FULL-synchronous six-row commit.
Only after successful commit does an internal publisher read the committed chain,
sample its own UTC clock and persist an append-only publication receipt.
The admission caller cannot supply this clock or published_at.

The receipt binds schema, bundle, exactly six sorted IDs, role, admission version,
exact observation bodies, committed ledger prefix, publication time and hash.
The ledger prefix is a content identity, so copying an intact ledger preserves replay.
No absolute file path is treated as scientific identity.

Row available_at/recorded_at remain physical admission metadata. Scientific Metrics
consumption requires an authenticated publication snapshot, with effective time
max(row/source causal availability, publication published_at). Rows alone fail.
Snapshot provenance includes the complete publication receipt; snapshot and replay
identities commit it. Derived replay uses the same effective time for Metrics nodes.

Crash after six rows but before receipt leaves six physical rows with no authority.
Reopening, snapshotting and repeated admission cannot create a missing receipt.
Exact readmission returns the original receipt; conflicting publications fail.
Historical v1 observations are unchanged and are not promoted to the new contract.

## Causal surface audit
- metrics_snapshot_gate: mandatory receipt plus existing exact six-row reconstruction.
- causal_observation_snapshot: authenticated ledger reader and effective time/provenance.
- causal_replay / causal_evidence_graph / latent context: consume that snapshot.
- causal_mechanics: uses gated snapshot; input_available_at now reflects effective time;
  reconstruction reauthenticates the original cutoff.
- derived_causal_replay: explicitly reauthenticates Metrics dependencies and records proof.
- Experiment 51 PM/PRM: authenticated reader; original S+5m raw cutoff unchanged.
- experiment51_sealed readiness: _gates -> _rebuild -> reconstruct -> derived;
  stored bindings cannot bypass current causal authentication.
- readiness_v2: capture coverage remains separate; scientific flags depend on sealed gates.
- generic observations_v2 causal gate already rejects raw Metrics, including derived
  dependency recursion. The frozen prospective_receipts.py was NOT modified.
- raw capture is not admission authority. No collector/protocol/retry changes.

## Trust and limitations
The internal clock and local admission boundary are trusted. Integrity hashes are
not signatures against an administrator rewriting both database and hashes.
Publication is usable only once its receipt transaction succeeds. Its published_at
is sampled after the atomic observation commit, as required by the additive contract.
No missing-time reconstruction, automatic crash recovery, historical retrofit,
real capture, outcome inspection or scientific promotion was performed.

## Local validation
- Reproduction before fix: 1 expected failure demonstrating the defect.
- First focused group: 98 passed.
- Related causal/role/Mechanics/Experiment51 group: 230 passed.
- Existing Windows partition: 179 passed, 2 existing skips (pythonw interpreter;
  unavailable Windows symlink privilege).
- Publication adversarial suite: 23 passed; with snapshot gate: 31 passed.
  Explicit Windows cases added to CI scope.
- Compile: PASS. Diff check: PASS (Git CRLF normalization warnings only).
- Full isolated CI: PENDING. No local WSL distribution / active Docker Linux engine.
  Existing GitHub CI requires publishing this candidate before it can qualify it.

Historical rows rewritten: NO. Retroactive receipts: NO. Real Metrics state mutated: NO.
METRICS_REAL_READY=NO; MECHANICS_REAL_READY=NO; EXPERIMENT_51_EXECUTED=NO.
REGIME_VALIDATED=NO; MECHANICS_VALIDATED=NO; POLICY_WINNER=NONE;
EDGE=NOT_DEMONSTRATED; REAL_CAPITAL_AUTHORIZED=NO.
