# STEP 48J.2 â€” Atomic Metrics admission into observations_v2

Status: PASS

## Purpose

STEP 48J.2 introduces the first causal admission boundary for the six-value
Metrics H1 bundle into observations_v2.

It does not perform network access, capture, scheduling, backfill, research-gate
evaluation, trading, outcomes, learning, knowledge or Criterion writes.

The admission authority remains the persisted Metrics H1 evidence reconstructed
through load_verified_bundle().

## Admission invariant

One verified Metrics H1 capture represents one logical six-value bundle.

Admission is atomic:

- six observations admitted together, or
- zero observations admitted.

Partial Metrics admission is forbidden.

The admitted features are:

- MarketMetrics/OpenInterest
- MarketMetrics/OpenInterestValue
- MarketMetrics/TopTraderAccountPositioning
- MarketMetrics/TopTraderPositionPositioning
- MarketMetrics/GlobalPositioning
- MarketMetrics/TakerBuySellRatio

All six observations share the same:

- bundle_id
- activation_id
- slot_id
- attempt_id
- result_id
- capture_receipt_id
- source period
- raw_bundle_sha256
- selected_rows_sha256
- capture availability authority
- ledger admission availability

## Authority and validation

Admission accepts only evidence reconstructed by load_verified_bundle().

The projection object alone is not admission authority.

Before persistence the implementation validates:

- exact verified bundle schema
- exact Metrics capture contract
- Binance USD-M provider
- BTCUSDT instrument
- complete six-value feature set
- exact component/field mapping
- finite strictly-positive values
- raw, non-derived semantics
- zero dependencies
- NOT_ADMITTED source state
- no prior claimed ledger availability
- exact five-minute source interval
- source-period end equal to slot
- causal chronology
- anti-backfill boundary
- component provenance
- exact component endpoints
- shared capture authority

The persisted source evidence is reloaded immediately before ledger admission.
If the reconstructed bundle identity or canonical content changes, admission fails.

## observations_v2 integrity

The existing observations_v2 chain is verified before admission and is verified
again inside the same BEGIN IMMEDIATE transaction used for persistence.

The transactional verification authenticates:

- previous_hash chain links
- receipt_hash chain digests
- row identity
- payload hashes

A failure aborts the complete Metrics transaction.

No existing observation is silently overwritten.

Semantic conflicts for the same instrument, feature, event time and source metric
time fail closed even when another source would produce a different observation id.

## Idempotence

An identical complete prior six-row admission is an explicit no-op:

ALREADY_ADMITTED

It does not append duplicate rows and does not modify the existing chain.

A partial prior admission is considered invalid and fails closed.

A conflicting prior admission fails closed.

## Availability semantics

capture_available_at remains capture provenance.

ledger available_at is assigned only at actual observations_v2 admission.

The Metrics source timestamp follows the frozen convention:

SLOT_MINUS_ONE_MICROSECOND

This is not receipt time and is not availability time.

## Validation

Initial focal implementation:
7 passed

Hardened focal implementation:
9 passed

Scientific-neighbor regression:
86 passed

The hardened tests cover:

- successful six-row atomic admission
- shared bundle identity
- shared ledger availability
- idempotent complete re-admission
- forced mid-transaction SQL failure with zero partial rows
- corrupted source evidence rejection
- future/unavailable evidence rejection
- historical backfill rejection
- pre-existing semantic conflict rejection
- mutation between initial projection and final admission
- observations_v2 corruption between preflight and transaction

Compile:
PASS

## Explicit non-claims

REAL_HTTP_EXECUTED=NO
REAL_RUNTIME_DEPLOYED=NO
TASK_REGISTERED=NO
REAL_METRICS_OBSERVATIONS_ADMITTED=NO

METRICS_OPERATIONAL_READINESS_81H=NO
FROZEN_OI_TAKER_RESEARCH_GATE_90D=NOT_EVALUATED

REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE
EDGE=NOT_DEMONSTRATED

## Checkpoint result

METRICS_OBSERVATIONS_V2_ADMISSION=IMPLEMENTED
ATOMIC_ADMISSION=PASS
PARTIAL_ADMISSION=FORBIDDEN
CAUSAL_AVAILABILITY=PASS
EVIDENCE_REVALIDATION=PASS
LEDGER_CHAIN_REVALIDATION=PASS

Full repository regression:
2295 passed, 4 skipped, 3 warnings

FULL_REPOSITORY_REGRESSION=PASS
METRICS_OBSERVATIONS_V2_ADMISSION=PASS
STEP_48J2_STATUS=PASS