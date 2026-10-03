# OMA-PNEP-1.0 Common Support Contract v1

Baseline: `85c199c92a8efe11caf5cc23f54dd326be64ef0e`.

`CommonSupportRegistry.register(opportunity, controls, decisions)` records causal
support for one existing EligibleDecisionOpportunity. It reuses PolicyKernel
formation and require_comparable; it does not authorize execution or evaluate
outcomes. No existing contract is changed.

## Admission and support

- Supply an immutable tuple of PolicyDecision objects, at most one per PolicyID.
- Every supplied decision must exactly match kernel formation for the supplied
  opportunity and SharedControls, including evidence, role, cut and provenance.
  Incompatible or forged decisions fail before registry mutation.
- Eligible policies have all authorized inputs causally usable according to the
  kernel. Missing, late, unknown and conflicting inputs remain ineligible without
  imputation. One policy's ineligibility does not remove other eligible policies.
- MISSING_DECISION means ABSENT, distinct from a present INELIGIBLE decision.
  Reference formation validates supplied decisions; it never fills absent ones.
- Empty and partial support are retained. `cs4` means all four policies are
  causally eligible. `supports((...))` tests an explicit subset. Neither grants
  operational authorization for Regime or Mechanics.

## Identity and freezing

The immutable record commits opportunity identity, role, decision time, controls,
full opportunity evidence, supplied decision identities, eligible policies and
exclusion reasons. Canonical policy order and kernel evidence canonicalization
make support identity independent of input ordering and process hash seed.
Changing absence to ineligibility changes the commitment even if eligible sets
coincide. No claim of mathematical collision impossibility is made.

The first snapshot is final, including partial/empty support. Exact replay is
idempotent; replacement, retrospective expansion or repair fails. The registry
reuses kernel cross-role event/cluster isolation. It returns immutable snapshots
and stores no mutable caller collections.

## Boundary and limitations

There are no outcome, return, performance, execution or ranking inputs. Only
population membership and causal comparability are represented. Upstream receipt
authenticity, evidence truth and scientific input validation remain upstream
responsibilities; hashes are commitments, not proof of semantic truth.

This is an in-memory contract, not durable capture or a population controller.
The experiment controller must submit the complete sampling population and freeze
support before outcome access. This API cannot detect deliberately omitted
opportunities/decisions or authenticate registration time. Separate registry
instances still require PNEP dataset-manifest isolation before combining data.
Production prevention of outcome-driven population selection is therefore not
claimed by this slice.

Validation uses synthetic fixtures only: focal Common Support and Policy Kernel
tests, plus PNEP contracts, blinding and sampling tests. No live datasets, holdouts
or outcomes are needed. Edge = NO; Regime validation = NO; Mechanics validation =
NO; no policy winner.
