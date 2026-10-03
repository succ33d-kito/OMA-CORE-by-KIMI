# OMA-PNEP-1.0 — Policy Kernel Contract v1

Baseline: `765ef0198575080fa08871486a035c74f2a122fd`.
Scope: outcome-blind formation records, not action selection, policy execution,
economic evaluation, market feature construction or promotion authority.

## Reuse and API

Reuses EligibleDecisionOpportunity, InputAvailabilityRecord, InputType,
InputStatus, PolicyID, PolicyDisposition and DatasetRole. Sampling is unchanged.
No market-state abstraction or replacement opportunity schema is introduced.

`PolicyKernel.form(opportunity, controls)` produces four frozen PolicyDecision
records from a single immutable opportunity snapshot. `require_comparable`
rejects heterogeneous controls, opportunity evidence or duplicate policy IDs.
There is no callback, payload loader, outcome store, network or operational path.

| Policy | Authorized families |
|---|---|
| P0 | EVENT, PRICE |
| PR | EVENT, PRICE, REGIME |
| PM | EVENT, PRICE, MECHANICS |
| PRM | EVENT, PRICE, REGIME, MECHANICS |

PolicyInformationSet contains detached InputEvidence commitments only. It does
not retain the opportunity or dependency objects. Access to a forbidden family
raises PermissionError; construction with extra/missing families fails closed.
Transitive dependency families must also be authorized; unavailable/forbidden
dependencies make the input unusable and remove its value commitment from view.

## Causality and support

Every usable assessment and dependency must be VALID, belong to the same
opportunity/cut/instrument/venue/product, and satisfy available_at <= decision_at.
UNKNOWN, MISSING, LATE and CONFLICT remain distinct and are never imputed.
Their assessment commitments remain auditable; their value hashes are hidden.

`information_set.causal_eligible` prepares causal support accounting by policy.
It is NOT operational authorization. Existing input_disposition gates remain
unchanged: PR/PM/PRM are operationally INPUT_INELIGIBLE in this slice even when
synthetic causal evidence is complete. No Regime/Mechanics gate is bypassed.
P0 may have None disposition, meaning unexecuted, never POLICY_ABSTAIN/ENTER.
No common-support economic calculations are implemented.

## Shared controls and identity

SharedControls requires explicit H1 timeframe, positive Decimal risk budget and
quote currency, policy-contract/risk/sizing/execution/accounting/transaction-cost
specification SHA-256 commitments and a positive horizon in seconds. There are
no economic defaults and no sizing or cost calculations.

The comparison identity binds full opportunity content (including protocol,
run, population rule, event/cluster, role, cut, instrument, venue/product and all
input evidence), explicit decision metadata and controls. Assessments are hashed
by full content, not just record_id. Family order is canonicalized. Decimal
serialization does not depend on the arithmetic context or round amounts.
Equivalent positive Decimal amounts (100, 100.00, 1E+2) have one commitment;
dependency edge order is canonicalized recursively without discarding evidence.
Identifiers remain exact opaque strings: no Unicode normalization or alias
merging is inferred. UTC-aware zero-offset timestamps serialize identically.

Decision identity additionally binds the policy information set and disposition.
Different controls or shared Event/Price evidence cannot be accepted as a fair
comparison. No random IDs, wall-clock reads or performance inputs are used.

The kernel context binds the first opportunity snapshot and its controls. An
incompatible later submission fails rather than repairing past eligibility.
Event/cluster reuse across dataset roles fails in the same context. Nothing
mutates, deletes or changes the role of the original opportunity.

## Trust boundaries and limitations

- This contract handles causal evidence/value commitments, not feature payloads
  or actual decision algorithms. No synthetic Regime/Mechanics values are made.
- A SHA-256 commitment does not authenticate source semantics, specification
  correctness or ex-ante registration. Upstream validators must guarantee family
  labeling, dataset provenance and specification freeze before real execution.
- In-memory contexts must be shared by compared policies; independent contexts
  still require existing dataset-manifest isolation before aggregation.
- An application API firewall cannot protect against hostile Python reflection,
  forged attestations, or manually fabricated formation records. Consumers must
  use kernel-produced records and the comparison validator.
- The whole-snapshot commitment is opaque audit context, not a feature resolver.
  Later policy execution must receive only the detached authorized view.

## Adversarial checks

Tests cover forbidden masks, transitive family leakage, invalid availability,
snapshot changes hidden behind identical record_id, shared-control changes,
cross-role reuse, mutable/inconsistent evidence, Decimal context independence,
replay, outcome kwargs and operational-import exclusion. Compilation is checked
without writing caches. No PIT capture, state, ledger, holdout or outcome is used.

Next bounded design step: define one shared outcome-blind decision rule consuming
only these views, with explicit gate proof and payload validation contracts before
any live authorization. This document does not implement or authorize that step.
