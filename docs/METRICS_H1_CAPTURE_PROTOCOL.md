# Metrics H1 prospective capture protocol v1

STEP 48B freezes a design, not an activated or qualified collector. Authority:
`METRICS_H1_RUNTIME_DESIGN.json`, canonical UTF-8 JSON (sorted keys, compact
separators, no trailing newline). Its SHA-256 commits every design field.
Starting checkpoint: `7419f7f45878067f4c5d85f7f2639bba080ccdc7`.

## Source and chronology

For BTCUSDT Binance USD-M, UTC hour boundary S requires the complete five-response
5-minute bundle ending **exactly at S**, representing [S-5m,S). Six values share
one logical capture attempt and availability boundary. The JSON maps all five
endpoints and six source fields to semantic feature identities.

Reuse `normalize_bundle`: OI and positioning timestamps label period ends;
taker labels period start. Existing normalization aligns to the nearest 300
seconds with at most 30 seconds displacement, then adds 300 seconds for taker.
Preserve original timestamps and normalized ends separately. Every normalized
end must equal S; the normalized metric timestamp is S minus one microsecond.
This timestamp is a source convention, **never a receipt or availability time**.
The future validator must authenticate these semantics against captured payloads.

Target = S+180 seconds; deadline = S+300 seconds. A first and only attempt may
start in [target,deadline). Every request must start at/after target; all complete
responses and durable bundle publication must finish at/before deadline.
Use actual aware UTC times, never caller-created historical receipt times.
Each request <= its full-body receipt <= shared availability <= deadline.
Bundle received_at is the maximum component receipt time. available_at is assigned
at actual durable publication; any uncertainty or publication past deadline
precludes SUCCESS. No timestamp clamping or backdating is permitted.

One bounded request per endpoint; no transport retry, redirect, pagination retry,
or same-slot retry. Request parameters must select the expected period (5m,
BTCUSDT) and preserve the returned full body. Exactly one matching row per
component is required; duplicates, missing rows, wrong symbol, invalid/nonpositive
values or mixed periods fail closed. Older/latest components cannot substitute.
Request timeouts are bounded by remaining time; late responses remain diagnostics,
not eligible evidence. HTTP 451 fails closed without fallback.

`fetch_once` is NOT the operational entrypoint: it requests Price and selects
latest-only metrics. `binance_research_collect.py` is research scaffolding, not
a daemon. Future implementation must isolate Metrics and enforce exact S.

## Evidence and identities

Persist exact full response bytes (base64), endpoint, parameters, HTTP status,
per-component request/receipt timestamps, raw source timestamps, normalized
period, hashes, and selected rows. `raw_bundle_sha256` is SHA-256 of canonical
JSON mapping endpoint paths to exact response-body base64 strings. Preserve the
existing selected-rows canonical JSON SHA separately; it is not a full-response
commitment. JSON hashes use sorted keys, compact separators, UTF-8, no NaN.

Slot identity commits contract, activation identity, instrument and UTC S.
Attempt identity commits slot identity (one attempt only); result identity commits
attempt identity and immutable terminal evidence. No random UUID, process address
or repr participates. Activation identity commits explicit dataset role and source
configuration; role cannot change on restart. All six features reference the same
slot, attempt, result, source interval, raw commitment and shared availability.
Partial admission is forbidden. Content conflicts fail closed, never overwrite.

## Activation, runtime and recovery

Only an explicit operator transaction may initialize an absolute external state
root ending `metrics-h1-v1`, preferably
`%USERPROFILE%\Documents\O-C data\prospective\metrics-h1-v1`.
Reject symlink/reparse ambiguity and any Price/Funding state alias. Freeze root,
role and activation slot: first UTC hour at/after activation time plus 600 seconds.
Runtime, adapter and installer cannot initialize. No state is created in STEP 48B.

Future module boundaries are listed in JSON; none is implemented here. Runtime:
LONG_RUNNING_AT_LOGON, task `OMA-CORE-Prospective-Metrics-H1`, IgnoreNew,
StartWhenAvailable, exclusive `runtime/runner.lock`, polling <=5 seconds.
`runtime/heartbeat.json` is liveness metadata, **not evidence**.
Runtime orchestrates only Metrics: no Price/Funding capture, outcomes, PnL,
LearningSignal, Knowledge, Criterion, orders or execution-state writes.

Persist attempt before network activity. SUCCESS requires verified complete
durable evidence; FAILED records a completed unsuccessful attempt; INCOMPLETE
means an attempt lacks a terminal result; MISSED_SLOT means no attempt occurred
before deadline; INVALID means failed integrity/contract verification. Immutable
artifacts are never edited to change these meanings; INVALID is terminal.
Continuity may derive INVALID from corrupted artifacts without rewriting them.

On clock regression, fail closed. A crash preserves INCOMPLETE or existing final
state. Never retry FAILED, complete old INCOMPLETE, or capture MISSED_SLOT.
Restart after deadline preserves absence and advances; restart inside a current
window attempts only if no attempt/final slot artifact exists. A process restart
does not reset the per-slot budget. No backfill, interpolation or historical repair.

## Readiness and research remain distinct

METRICS_OPERATIONAL_READINESS_81H requires 81 consecutive UTC H1 SUCCESS slots
computed from verified persisted artifacts, never heartbeat. Missing, FAILED,
MISSED_SLOT, INCOMPLETE and INVALID break the streak. This is
DATA_PLANE_READINESS_ONLY, not a research result.

FROZEN_OI_TAKER_RESEARCH_GATE_90D remains governed only by
`research/metrics_2024_2025/PROSPECTIVE_H1_PREREGISTRATION.json`, SHA-256
`012a80dcfd4566c7906c61a03f2c5ce3991c31481d2bdb4d87e6855d6005bc46`.
Reference facts (not a replacement protocol): registered 2026-09-29T20:54:01Z;
holdout starts 2026-10-01T00:00:00Z; 2160 hours/90 days; decision S+5 minutes;
bar and metrics available by decision; source timestamp <S, age <=60 minutes;
no imputation. Primary horizon 4h, family 1/4/12/24/48h, minimum N=200 target
and 200 comparator per horizon. The preregistration and its start are unchanged.
Uncaptured time before qualified activation remains absent prospective evidence.
This checkpoint neither opens holdout data nor evaluates this gate.

## Future observations_v2 boundary

DESIGNED_NOT_IMPLEMENTED. Current raw causal admission remains Price/OHLCV and
FundingRate/Published. Metrics remain UNKNOWN until a validator authenticates
version, provider, BTCUSDT, exact source/slot relationship, complete aligned bundle,
raw bytes/hash and recomputed values, chronology within the entire window,
immutable SUCCESS, role, no backfill/conflict and no derived dependencies.
Adding feature strings alone is forbidden. Legacy metric receipts cannot be
promoted automatically. No production admission code changes in STEP 48B.

UNKNOWN != 0. Funding rate != funding cashflow. Raw score != probability.
Historical data without independent receipt evidence is not prospective evidence.
EDGE=NOT_DEMONSTRATED; REGIME_VALIDATED=NO; MECHANICS_VALIDATED=NO;
POLICY_WINNER=NONE. Publication of this specification proves no operational capture.
