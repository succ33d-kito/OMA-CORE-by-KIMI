# Official Manifest Binding v1

Baseline: `0d22ba6f324e499ccf66d1c381b789bd75359946`.

## Authority and scope

Designate one custody directory for the experiment before outcome access.
`OfficialManifestStore(directory).bind(scope, manifest, bound_at)` creates or
verifies the official declaration. An in-memory OfficialManifestBinding object
alone is not registration; successful persistence/verification is required.

Logical scope is existing `(protocol_id, run_id, dataset_role)`. A run identifies
the experimental batch. Protocol hash, population-rule hash and cutoff are bound
attributes, deliberately not scope escape hatches: changing them within a run and
role conflicts with its original official declaration. Instrument/timeframe are
already committed in the manifest; no additional scope taxonomy is introduced.

The caller must pass the exact PopulationScope matching the manifest, including
role. Only the exact FROZEN ExperimentalPopulationManifest type is accepted; no
auto-freeze. Existing PNEP contracts are unchanged.

## Commitments and time

The binding commits full scope, manifest_id, manifest artifact_id, digest of its
canonical JSON and frozen_at. It stores no population copy. Keep the original
manifest artifact alongside the declaration under the experiment's custody rules.
The full content digest and artifact ID prevent substitution of another freeze
artifact even when its scientific manifest_id is unchanged.

Require UTC-aware `population_cutoff <= frozen_at <= bound_at`. Caller timestamps
are assertions, not authenticated chronology. Binding identity excludes bound_at
so retries do not create new identities. Binding artifact identity includes it.
An identical retry returns the first persisted declaration and timestamp; a retry
timestamp preceding the recorded binding fails. No wall clock is fabricated.

## Create once

The filename is scope_id plus `.json`, derived internally, never caller-selected
per binding. Exclusive file creation prevents concurrent competing writers from
both winning. Flush/fsync completes before returning a newly registered binding.

An existing file must exactly equal the canonical expected binding using its
original bound_at. Different manifest/content, unknown fields, invalid content or
incomplete writes fail closed and are preserved. No overwrite, truncation,
replacement, delete, repair, amendment or last-write-wins API exists. A concurrent
reader can reject an incomplete in-progress file; retry after successful creation
is safe. Power-loss recovery/directory durability guarantees are outside v1.

## Trust limits

This prevents rebind through the supported API **within the designated authority
directory**. It cannot stop external deletion/editing, filesystem/clock compromise,
Python reflection/monkeypatching or an unrestricted operator. Nor does it detect
renaming an experiment/run or choosing another directory and calling it official.
External custody must fix that authority and attest publication chronology.

There is no outcome input, callback, performance metadata or outcome access.
Binding must precede outcomes; this contract does not itself control access to
them or prove that the operator had not already observed results. No downstream
scientific validity is inferred from registration or caller-supplied commitments.

## Validation and next boundary

Synthetic tests cover frozen-only admission, scope/role mismatch, rebind,
cutoff/version evasion, same-ID artifact substitution, subclass spoofing, retries,
immutable inputs, concurrent creation, damaged-file preservation and process/order
determinism. Integration is limited to Experimental Manifest tests.

This closes the planned defensive slice. Next work should return to a minimal
experimental decision-rule specification using these fixed population contracts;
no new general registry/controller is proposed here.

Edge = NO. Regime validation = NO. Mechanics validation = NO. Policy winner = NONE.
