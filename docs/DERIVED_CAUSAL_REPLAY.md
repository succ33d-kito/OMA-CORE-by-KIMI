# Derived causal feature layer v1

Raw 49A identity/contracts remain unchanged. A separate `derived-causal-replay-v1`
certificate commits explicit role, cutoff, reconstructed Regime/Mechanics IDs,
transitive dependency IDs and canonical graph content. Persisted raw dependencies
are source nodes, attestations evidence nodes and derived features market-state
nodes. The only modification to the existing graph store is the additive typed
relation `derived_feature_from`, allowing evidence/market-state dependencies on
sources or derived evidence/market-state. Existing relations/identities are intact.

`replay_derived_features` validates every selected derivative before graph append.
Each graph node commits the exact persisted envelope. Edges identify exact
dependencies and become available with their derived source. The graph writer
retains immutable conflict checks and endpoint availability checks.

`reconcile_derived_replay` independently rebuilds two temporary graph stores and
requires identical certificates. Certificate identity excludes unrelated existing
graph contents and later ledger rows. Role mismatch is unavailable, not relabeled.
Future computed derivatives are absent from historical as-of projections.
Returned dictionaries are detached representations, not trusted authorization
objects: consumers must revalidate against the ledger. Local hash commitments
prove consistency under the existing trusted capture boundary, not external
cryptographic attestation of a maliciously replaced entire database.

No capture, 81H operational qualification, scientific validation or Edge claim.
