# Explicit dataset-role isolation in causal reconstruction

Snapshot, replay and reconciliation accept an explicit
`dataset_role=PILOT/DISCOVERY/CONFIRMATION`; the operator CLI accepts `--role`.

The requested role enters snapshot and replay commitments even when no eligible
observations exist. It propagates through both independent reconciliation runs.
Unknown or incompatible roles fail closed. Source observations are never
retrospectively relabelled, rewritten or re-admitted.

## Authenticated role boundaries

Three causal evidence families now have explicit role-authentication boundaries
for new observations:

- **MarketMetrics/** - the complete six-value H1 admission bundle authenticates
  its dataset role. Partial or inconsistent bundle membership cannot enter the
  causal snapshot.
- **FundingRate/Published** - new Funding observations carry
  `funding-dataset-role-auth-v1` provenance tied to the exact capture identity.
  Legacy roleless Funding remains available only to unscoped diagnostic views.
- **Price/OHLCV** - the frozen Price capture remains unchanged and roleless.
  A separate prospective authority chain provides:
  `PriceRoleActivation -> pre-capture authorization -> exact raw Price
  observation -> PriceRoleAttestation`.
  The attestation depends on the exact Price observation and proves that the
  authorization strictly preceded the earliest persisted capture evidence.
  Legacy Price remains unscoped only.

No dataset role is inferred from source URL, filesystem path, caller, current
operating mode, state directory or historical intent.

## Price attestation semantics

`PriceRoleAttestation/v1` is provenance/authority metadata, not a market feature.
It is never projected as economic evidence.

For a role-scoped Price observation to enter a causal snapshot:

1. the raw Price observation must pass its frozen semantic/causal contract;
2. the exact derived role attestation must exist by the requested cutoff;
3. activation, authorization, Price commitment and dataset role must all verify;
4. the requested role must exactly match the attested role.

A Price observation cannot be relabelled by replacing the snapshot role or by
stripping its embedded role proof.

The persisted evidence supports the precise claim that authorization strictly
precedes the **earliest persisted capture evidence**. It does not claim that the
authorization timestamp cryptographically proves precedence over every internal
network action on a hostile machine.

## Unscoped compatibility

Omitting `dataset_role` retains the prior diagnostic projection behavior.

Unscoped mode does **not** certify dataset isolation and must not be used as proof
of experimental eligibility. Legacy roleless Price/Funding may remain visible
there when they independently pass their semantic causal gates.

Role-specific snapshots, replay certificates and reconciliation identities are
separate commitments from unscoped reconstruction.

## Replay and reconciliation

Authenticated role selection propagates through:

`observations_v2 -> causal snapshot -> latent projection -> EvidenceGraph
-> deterministic replay -> independent replay reconciliation`

Reconciliation executes two reconstructions with fresh graph stores and compares
the complete serialized replay certificates.

`MATCH` means deterministic reconstruction equivalence only. It is not provider
truth, causal identification, prediction quality, Regime validation, Mechanics
validation or demonstrated Edge.

Explicit closeout regression coverage proves:

- authenticated PILOT Price survives through replay and reconciliation;
- the same Price requested under the wrong role remains missing;
- an attestation unavailable at the cutoff remains missing through replay;
- historical/legacy roleless evidence is not retroactively promoted;
- attestation metadata never becomes a market feature.

## 49A / 49B status

Within the scoped causal-observation and deterministic-replay contracts:

- **49A - Causal Observation Fabric: COMPLETE**
- **49B - Deterministic Replay & Reconciliation: COMPLETE**

This status does not imply broad Event Intelligence / WorldState integration,
Regime or Mechanics validation, experimental Edge, operational readiness of the
81-hour Metrics gate, OMA-CORE v1 completion, or real-capital authorization.

The next research integration boundary is causal Regime/Mechanics work under the
same role-isolation and temporal-integrity rules.
