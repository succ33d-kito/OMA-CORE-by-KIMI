# Explicit dataset-role isolation in causal reconstruction

Snapshot, replay and reconciliation accept dataset_role=PILOT/DISCOVERY/CONFIRMATION;
CLI accepts --role. The requested role enters snapshot/replay commitments even for
an empty result. It propagates through both independent reconstructions. Unknown
or incompatible roles cannot silently become the selected role. Source rows are
not relabelled, updated or re-admitted.

Currently only the complete Metrics admission envelope authenticates a ledger
role under this projection contract. The existing Price/Funding bridge does not
persist an equivalent explicit role commitment. Role-scoped reconstruction excludes
these observations, even when they independently pass their semantic causal gate.
No inference from source paths, old capture intent or current operating mode.

Omitting role retains the prior diagnostic projection and its identity format.
That unscoped mode does NOT certify dataset isolation and must not be used as proof
of experimental eligibility. Explicit role is an optional extension to the existing
v1 serialized contract; old unscoped certificates omit the field unchanged.
A MATCH with no eligible observations proves empty reconstruction consistency only,
not completeness or readiness. Missing features remain explicit.

Tests cover PILOT versus DISCOVERY/CONFIRMATION, empty identities, invalid role,
constructor relabelling, both replay branches, CLI propagation and verified Funding
without preserved role. No LIVE changes, source writes, captures or holdout access.

Next prerequisite: freeze and implement versioned role-bearing Price/Funding
admission provenance for NEW observations. Do not retrofit historical rows. Until
then scoped snapshots intentionally lack those inputs, and dependent hypotheses
must remain blocked. This does not validate Regime, Mechanics or Edge.

Validation: 58 distinct focal/direct-boundary tests passed (41 + 16, then 8 role tests including one added CLI regression). Compile and diff check PASS. No full-suite rerun in this bounded checkpoint.
