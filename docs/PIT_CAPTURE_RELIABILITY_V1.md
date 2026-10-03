# PIT Capture Reliability / Clock Health v1

Live price admission requires fresh evidence from Binance's HTTPS serverTime
endpoint. The host wall clock must never precede that server timestamp. The
server timestamp must be no more than one second behind the host receipt
time; monotonic round-trip time must be at most two seconds. Wall and
monotonic elapsed time must agree within 100 ms through admission. Failure
rejects the attempt without correcting any clock or substituting timestamps.
These conservative operational limits may reject slow networks. HTTPS provider
time is a provider reference, not an independent NTP certification. Historical
receipts and the existing causal verifier are unchanged.

Each retry obtains new time evidence and actual response receipt times, for the
same scheduled event only. Failed attempts may retry every 20 seconds within
the existing two-minute window after the delayed slot; conflicts stop retries.
Admission rechecks the deadline. No resumed process catches up historical slots.
Network timeout is bounded per request but is not a hard total HTTP deadline;
late returns are rejected at admission. Missed slots remain scientific gaps.

Status retains capture_running and adds HEALTHY/DEGRADED/UNHEALTHY,
capture_healthy, last_success_at, receipt_age_seconds, heartbeat_age_seconds,
consecutive_failures, missed_slots and clock_failures. Health requires a live
process, PASS integrity, heartbeat within 60 seconds, receipt within 3725
seconds, and no failed attempts since the last success. Missing initial evidence is degraded;
a stopped process, stale heartbeat, clock regression or latest clock failure is
unhealthy. Counters describe retained attempt files, not periods before logging
began. Status remains a snapshot, not proof of successful future capture.

`run --keep-awake` optionally requests Windows ES_SYSTEM_REQUIRED for the runner
thread and releases it in finally. It changes no global power settings and does
not prevent explicit sleep, shutdown or lid actions. It is off by default.

Deploy only after stopping the old runner through the usual operator procedure.
This development cut does not restart a live runner, synchronize Windows time,
contact the provider, or inspect/write production ledgers during tests.

Adversarial review clarification: the offset interval is [host request start -
serverTime, host response receipt - serverTime]. Its upper bound must be <= 1s;
serverTime after host receipt is rejected. This is conditional on the provider
stamping the response during the request; HTTPS authenticates the provider, not
its clock. Latency can conceal a small host lag. HEALTHY means these operational
checks passed, not that true UTC offset is known to be zero. Every measured
checkpoint and segment must agree with monotonic time; unseen compensated jumps
between samples and changes within the 100ms tolerance cannot be excluded.
Deadline is checked before each request and response and after the SQLite writer
lock. received_at remains the response receipt; available_at is assigned after
the writer lock. Exhausted retry slots are recorded as MISSED_SLOT; this never
writes a receipt or fills a historical gap. Server-ahead is an attempt-level
CLOCK rejection, not a diagnosis of persistent Windows/NTP desynchronization.
