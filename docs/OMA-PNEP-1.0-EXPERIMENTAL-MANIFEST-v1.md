# Experimental Population Freeze / Manifest v1

Baseline: `eaf4d148043e46d7c6eac5c3bdaceb3d1b1d3e2a`.

## Contract

`PopulationScope` fixes protocol ID/hash, run ID, existing DatasetRole,
population-rule hash and UTC population cutoff. Protocol/rule hashes commit their
versioned specifications; there is no alternate role or hashing system.

`PopulationManifestBuilder.add(opportunity, controls, decisions, support)` admits
an existing opportunity and Common Support snapshot. It checks scope, duplicates,
decision time and all assessment/dependency timestamps against cutoff. Existing
Policy Kernel/Common Support validation verifies the supplied snapshot against
the same evidence; it does not substitute newly formed support for absent policies.
Even receipts used only to revise an exclusion must not postdate cutoff.

Admission includes empty and partial support without filtering. Policy decision
commitments, full opportunity commitment, shared controls, support identity,
eligibility and exclusion reasons are retained. ABSENT and INELIGIBLE remain
distinct. Invalid admission does not change the builder.

`freeze(frozen_at)` transitions BUILDING to FROZEN. Frozen time must be UTC and at
or after population cutoff. Exact freeze replay returns the original object;
another time or any later addition fails. There is no remove/update method.
Frozen records, scope and nested collections are immutable through the supported
API. Canonical opportunity order eliminates input-order effects; duplicates fail
rather than being silently deduplicated.

## Artifact and identity

`manifest_id` commits the scope and complete ordered support snapshots. Membership,
scope or commitment changes produce a different commitment. `frozen_at` is
materialization metadata, separate from scientific population identity:
`artifact_id` additionally commits frozen time and state. Thus independent
materializations of the same population have the same manifest ID.

`to_json()` serializes the full committed representation with schema version.
Record tuple layout follows `_support_payload`: opportunity ID, role, decision
time, comparison ID, controls commitment, opportunity commitment, eligible
policies, exclusions, policy decision commitments, support ID. Scope tuple order
is protocol ID/hash, run ID, role, population-rule hash, cutoff.
`write_exclusive(path)` writes a new file and refuses an existing destination.
No dataset or ledger is read or written automatically. No reader/recovery engine
is implemented; the JSON preserves the original committed representation.

## Trust boundary and later corrections

Use the builder, freeze and preserve the artifact **before** outcome access.
Neither caller-supplied timestamps nor a content hash independently prove real
chronology. External custody/publication is required to attest the freeze time
and bind one official artifact to the experimental scope. The primitive does not
prevent a malicious caller from omitting observations, creating another builder,
backdating timestamps or editing files outside its API. It detects changed content
through commitments; it is not an outcome-access controller or tamper-proof store.
Upstream provenance truth, population-rule execution and cross-run dataset/shock
isolation remain responsibilities of existing sampling/manifests and the future
controller. Public dataclass construction is not an authenticity certificate.

Amendments/invalidation must be separate append-only artifacts referencing the
original manifest and artifact IDs, with reason and new timestamp. Never replace
the original or treat the amended population as the original preregistration.
Amendment code is deliberately deferred.

## Validation and scientific interpretation

Synthetic tests cover ordering/process independence, membership and commitment
sensitivity, scope mismatch, duplicates, immutable freeze, exclusive export,
cutoff/UTC, ABSENT versus INELIGIBLE and rejection of outcome arguments. Focal
integration uses Common Support and Policy Kernel tests; no outcomes are needed.

Edge = NO. Regime validation = NO. Mechanics validation = NO.
Policy winner = NONE. This artifact protects population integrity; it does not
establish profitability or validate any policy.
