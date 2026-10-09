# Funding Prospective Capture Protocol v1

Status: PROTOCOL_FROZEN / NOT_ACTIVATED

## Purpose

Define the prospective BTCUSDT Binance USD-M premiumIndex capture schedule
and continuity semantics before any new live Funding capture is activated.

This protocol governs capture evidence only.

It does not validate Regime, Mechanics, a trading policy, or economic Edge.

A published funding rate is not a funding payment or funding cashflow.

## Scope

Contract: funding-h1-capture-v1

Instrument: BTCUSDT

Venue: Binance USD-M

Endpoint:
https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT

Dataset role: PILOT

Capture primitive:
premium_index_capture.capture_premium(new_directory)

Verification primitive:
premium_index_capture.load_premium(directory)

Ledger adapter:
funding_rate_observation.append_verified_funding_rate_observation

Real observations_v2 write:
DISABLED during protocol and runner qualification

## Slot identity and cadence

Funding continuity is slot continuity.

It is not a claim that provider exchange_at timestamps are exactly one hour
apart.

Cadence:
H1

Time basis:
UTC

Slot boundary:
exact UTC hour HH:00:00

Scheduled capture target:
slot boundary + 15 seconds

Slot deadline:
slot boundary + 2 minutes

Slot id:
YYYYMMDDTHH0000Z

The slot id is derived only from the H1 slot boundary.

There is one authoritative attempt identity per slot.

A request may start only at or after the scheduled target and before the
slot deadline.

A request after the slot deadline cannot repair that slot.

The +15 second target is frozen before activation and must not be optimized
from outcomes.

## Activation epoch

The runner configuration must record an immutable activation_slot before the
first live run.

Only slots at or after activation_slot can contribute to continuity.

Captures created before activation_slot, including the 2026-10-05 premium
artifacts, remain audit evidence only.

They cannot be imported, relabeled, replayed, or counted toward this protocol.

## Attempt state

Every expected slot has exactly one immutable attempt directory:

attempts/YYYYMMDDTHH0000Z/

The attempt may contain:

attempt.json
    slot identity and STARTED evidence

capture/
    raw premiumIndex capture artifacts when a request was attempted

result.json
    immutable final result when finalization occurred

Allowed final semantic states:

SUCCESS
    One capture exists, load_premium verifies it, source and scope match,
    and the capture belongs to the live slot attempt.

FAILED
    The one live attempt failed transport, validation, clock, persistence,
    or contract checks.

MISSED_SLOT
    The slot deadline passed without a valid live attempt.

INCOMPLETE
    Recovery finds STARTED evidence without a valid immutable final result.
    This is preserved and never rewritten as success.

INCOMPLETE is a recovery classification, not permission to mutate an old
attempt.

## Retry and recovery policy

Retry policy:
NONE within the same slot.

A failed request is evidence of a failed slot.

It is not permission to replace it with a later request.

A transport outage must not disable future slots.

The runner advances to the next future slot after preserving the failure.

After restart or host suspension:

old slots are never captured

old FAILED slots are never retried

old INCOMPLETE attempts are never completed retrospectively

due slots without an attempt are represented as MISSED_SLOT

no backfill is allowed

no interpolation is allowed

no synthetic availability is allowed

no continuity repair is allowed

## Capture chronology

For every SUCCESS:

exchange_at <= received_at <= capture_available_at

When real ledger integration is later enabled:

exchange_at
<= received_at
<= capture_available_at
<= ledger_available_at

nextFundingTime is provider schedule metadata only.

It is never capture availability.

## Continuity accounting

The authoritative continuity unit is the expected H1 slot.

A slot counts as valid only when all of the following are true:

slot >= activation_slot

exactly one authoritative attempt exists for the slot

final state is SUCCESS

capture artifacts reopen successfully through load_premium

capture source, instrument, role and schema satisfy frozen contracts

request_started_at >= slot + 15 seconds

request_started_at < slot + 2 minutes

received_at and capture_available_at preserve causal chronology

no duplicate exists

no replacement exists

no conflict exists

no retrospective repair exists

no synthetic timestamp exists

FAILED, MISSED_SLOT, INCOMPLETE, duplicate, conflict, or invalid evidence
breaks the current continuity streak.

A later SUCCESS begins a new streak.

Gaps are preserved permanently.

## Readiness gate

READINESS_WINDOW_SLOTS = 81

funding_81h_ready is true only when the most recent 81 due H1 slots are
consecutive valid SUCCESS slots under this protocol.

The readiness report must expose at least:

total_expected_slots
successful_slots
failed_slots
missed_slots
incomplete_slots
invalid_slots
duplicate_slots
current_streak
longest_streak
slots_to_81
first_valid_slot
last_valid_slot
funding_81h_ready

When funding_81h_ready is true, a deterministic certificate may identify
exactly the 81 slot ids and verified capture identities used.

This is DATA-PLANE READINESS ONLY.

It does not establish predictive value.

It does not establish Regime validation.

It does not establish Mechanics validation.

It does not establish economic qualification.

It does not establish Edge.

## Failure semantics

UNKNOWN is not zero.

A missing Funding capture is not a zero funding rate.

FAILED, MISSED_SLOT, and INCOMPLETE slots are not silently omitted from
continuity accounting.

Published funding rate is not funding payment.

Funding rate is not funding cashflow.

Funding cashflow remains UNKNOWN unless a separate causal payment and
exposure contract is later established.

## Runtime and scheduling boundary

The future runner may reuse the existing OMA long-running Windows task pattern,
runner lock, heartbeat, immutable attempt directories, and fail-closed clock
semantics.

It must use a distinct task name and state root from Price.

Planned task identity:

OMA-CORE-Prospective-Funding-H1

Planned state root:

C:\Users\PC\Documents\O-C data\prospective\funding-h1-v1

Step 47B does not create this task.

Step 47B performs no HTTP.

Step 47B writes no observations_v2 rows.

## Scientific status after protocol freeze

FUNDING_CAPTURE_PROTOCOL = FROZEN

FUNDING_LIVE_CAPTURE = NOT_ACTIVATED

FUNDING_REAL_LEDGER_INTEGRATION = NO

FUNDING_CONTINUITY = NOT_ESTABLISHED

FUNDING_CASHFLOW_OBSERVED = NO

REGIME_VALIDATED = NO

MECHANICS_VALIDATED = NO

POLICY_WINNER = NONE

EDGE = NOT_DEMONSTRATED
