# Experiment 51: SEC prospective document discovery v1

Baseline: 845625ce4c08548270f058eb07a0980850ea4240.
Source authorized by project owner: SEC_OFFICIAL_PRESS_RELEASES_RSS_V1, PILOT.

## Frozen source and chronology

Verified 2026-10-13: https://www.sec.gov/newsroom/press-releases directly links
https://www.sec.gov/news/pressreleases.rss. Local preflight returned HTTP 200,
application/rss+xml. Preflight is not a prospective receipt or watermark.
SEC publishes RSS for subscriptions: https://www.sec.gov/about/rss-feeds.

Authority commits the exact feed, www.sec.gov host, /newsroom/press-releases/
child path, parser, identified User-Agent, 300-second polling, PILOT role,
operator binding and source-journal path. Activation uses internal time and
exclusive creation. The existing EventDirection authority is not modified.

First successful parsed feed establishes an immutable baseline. Baseline GUIDs
OR document links remain excluded forever, including later changed entries.
No baseline child document is fetched. An empty/invalid feed is not a watermark.
A crash between initial feed persistence and baseline publication fails closed;
there is no automatic repair/rebaselining.

Each later poll writes an attempt, bounded feed bytes/hash, observation time and
metadata. All new discoveries are persisted before document downloads. A durable
previous feed retains first-observation time after an interrupted poll; publication
metadata never supplies availability. There is no arbitrary child-URL public API.

Every new release is captured regardless of topic. Once discovered, documents
still visible in the current feed are checked once per normal poll for revisions.
Off-feed documents are not crawled. Thus revisions not observable in the feed
window are not claimed to have been detected. Same GUID with different URL, or
same prospective URL with changed GUID, fails closed. All redirects are rejected.

Document requests are sequential with at least one second per request, identified
User-Agent, 20-second timeout and 4 MiB maximum. Complete UTF-8 HTML/plain entities
are preserved. HTTP completeness is not independent proof of semantic truth.
403/429/503 stops further document requests for that poll. No invocation retries.
The next scheduled poll may attempt unresolved documents, preserving original
discovery and using its actual later fetch receipt timestamp.

## Canonical integration and isolation

Canonical RealEventStore rows retain receipt identity, content, hash, source
commitment, role, internally sampled fetch receipt and durable-ready availability.
Discovery receipts additionally authenticate the authority, original feed/item,
current feed, source binding and revision chain. A revision appends a new receipt
and prior-receipt reference; unchanged bytes preserve the first receipt. Interrupted
ready publication remains UNKNOWN. Legacy exact-source behavior remains unchanged;
legacy capture cannot bypass a discovery-authorized child source.

Source/admission journal uses the path already bound by EventDirection:
`<OMA_DATA_ROOT>/prospective/event/experiment51-source-pilot-20261013.sqlite`.
Discovery uses a separate `experiment51-sec-discovery-pilot-20261013/discovery.sqlite`
and an OS-held poll.lock. Process termination releases the OS lock, not history.
Overlapping invocation fails before attempting HTTP. Every started poll is visible,
including an INCOMPLETE attempt after termination. Earliest repeat is 300 seconds.

Read-only inbox returns literal document content, identities, chronology and
admission/attestation state only. It is not a recommendation. It does not import
NewsAgent, Council or outcomes. Generic releases await explicit manual admission;
Bitcoin mentions never create direction. Existing AdmissionEvidence, sampling,
shock reservation, EventDirection and P0 contracts remain authoritative.

CLI: `scripts/sec_event_discovery.py --root <discovery-root>` with `activate`,
`poll`, `status`, `inbox`, `admit`. Activation requires `--operator-root`.
Manual admission requires `--receipt-id` and `--evidence-json` containing the
existing AdmissionEvidence fields. Direction continues through the existing
`scripts/event_direction_operator.py ... attest` command with explicit curator
assertion. Late semantic processing is rejected by the existing reservation;
no cutoff rollover, outcome lookups or automatic classification is introduced.

Test-process guards reject production prospective paths before I/O. Fixtures use
temporary journals and private transport monkeypatches. No production fixture
fallback exists. These guards and local hash chains are not hostile-process
security: filesystem custody, clock integrity and truthful human semantics remain
external trust requirements.

## Scheduled deployment

Installer: scripts/install_sec_event_discovery_task.ps1. Requires successful
baseline, verified status and no existing task of the same name. Uses explicit
Python 3.11, immutable runtime checkout, working directory and state root.
One task: OMA-CORE-Experiment51-SEC-Event-Discovery; 5-minute one-shot repetition;
IgnoreNew; 4-minute execution limit; interactive user token; battery allowed.
No wake-from-sleep, catch-up, login-independent operation or liveness inferred
from a task name is claimed. Gaps remain gaps. Price/Metrics tasks are untouched.

## Qualification and operational checkpoint

Recorded after tests and CI, before real activation. No Experiment 51 outcomes
are inspected. SOURCE_DISCOVERY is a PILOT ingestion authority, not activation
of the Experiment 51 DISCOVERY dataset phase.

EXPERIMENT_51_EXECUTED=NO. DISCOVERY_ACTIVATED=NO. REGIME_VALIDATED=NO.
MECHANICS_VALIDATED=NO. POLICY_WINNER=NONE. EDGE=NOT_DEMONSTRATED.
REAL_CAPITAL_AUTHORIZED=NO.
## Local qualification

Implementation: 6a9bdca6852a3f78b361e65bc23640cf72f68d0f.
New discovery tests: 47 passed. Legacy RealEventReceipt: 28 passed.
Combined focal result: 75 passed in 37.77s.
Directly related integration: 369 passed in 78.17s.
Windows partition: 179 passed, 2 skipped in 82.37s.
Existing Windows skips: interpreter includes pythonw; symlink privilege unavailable
(reparse regression covered). Suite counts overlap and must not be added as unique
coverage. Four changed Python files compiled; PowerShell installer parsed;
git diff --check passed. No predictive outcomes were inspected.

Adversarial corrections during qualification: canonical dictionary-order-independent
contract hash; discovery-scope bypass through legacy authorization blocked even
before first receipt; exclusive source binding; all discoveries committed before
document requests; interrupted initial watermark refuses automatic repair;
interrupted ready marker remains UNKNOWN; GUID/link conflicts fail closed.

Preregistration canonical hash remains
7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8.
Pre-deployment EventDirection authority file SHA-256:
9CF162F7C93415811DD472AE4E610F08F61F4EDAF945147D961E4C40C7FC0FEE.
## Published qualification and real activation

Full isolated CI PASS for implementation 6a9bdca6852a3f78b361e65bc23640cf72f68d0f:
https://github.com/succ33d-kito/OMA-CORE-by-KIMI/actions/runs/38481644688
2486 passed, 197 skipped, 3 warnings in 210.09s. Skips: 181 Windows partition
nodes, four Windows activation fixtures qualified locally, 12 unavailable network
OHLCV cases. Pytest warnings concern existing class-scoped fixture deprecation;
Actions also emitted Node deprecation notices. No full-suite failure.

Source authority activated AFTER qualification:
- authority_id: 911c62049403922a473c28438bc0825594243fa498543770ed16e0f85ca87ac2
- activated_at: 2026-10-13T23:06:46.237434+00:00
- role: PILOT
- contract_hash: 831c49f02d82112986bdbda352c5f2599e4383a2cafd370fd9ef78e2560772aa
- endpoint_hash: 5c59ef6d1ff54cd19d40f0909b66f707f55fbe2e942928cea0fd8dfdbc2e5e4c
- authority/discovery journal:
  <OMA_DATA_ROOT>/prospective/event/experiment51-sec-discovery-pilot-20261013/discovery.sqlite
- canonical receipt/admission journal:
  <OMA_DATA_ROOT>/prospective/event/experiment51-source-pilot-20261013.sqlite

One real baseline poll began 2026-10-13T23:06:47.839295+00:00;
feed received 2026-10-13T23:06:48.683254+00:00.
SUCCESS_NO_NEW_ITEMS. 25 baseline items. Zero child documents fetched;
zero prospective receipts, candidates or attestations.
Baseline commitment: a58047c24e2174511896fe923049fcc8c8feaee3127f6099f81b847d97b778ec.
Read-only journal verification: PASS.

Scheduled task verified enabled, Ready:
OMA-CORE-Experiment51-SEC-Event-Discovery.
Interpreter: <QUALIFIED_PYTHON>.
Script: <OMA_CORE_RUNTIME_SEC51>/scripts/sec_event_discovery.py.
Working directory: <OMA_CORE_RUNTIME_SEC51>.
Arguments: -B <script> --root <discovery directory above> poll.
Runtime detached checkout: 6a9bdca6852a3f78b361e65bc23640cf72f68d0f.
Interval PT5M, IgnoreNew, execution limit PT4M. Next run at verification:
2026-10-13T23:12:11Z. LastTaskResult 267011 (0x41303, not yet run).
This verifies manual smoke success and scheduler arming, not a completed scheduled
invocation. No indefinite waiting or extra manual poll was performed.

Read-only readiness at 2026-10-13T23:07:59.103271+00:00:
Price: 29 valid contiguous H1, integrity PASS; 81H gate NO.
Metrics: 55 valid, streak 7, longest 12; capture is not derived admission.
EventDirection authority remains ACTIVE, same ID and exact original file hash.
Bound Event population and P0-eligible opportunities remain zero.
LIVE, Price runtime and SEC runtime worktrees verified clean.

SOURCE_DISCOVERY_V1_IMPLEMENTED=YES. SOURCE_DISCOVERY_V1_QUALIFIED=YES.
SOURCE_DISCOVERY_AUTHORITY_ACTIVATED=YES. INITIAL_BASELINE_ESTABLISHED=YES.
EVENT_DISCOVERY_RUNTIME_ACTIVE=YES (armed, first scheduled run pending).
NEW_PROSPECTIVE_DOCUMENTS=0. POST_ACTIVATION_EVENT_RECEIPTS=0.
ADMITTED_EVENT_CANDIDATES=0. UNATTESTED_EVENT_CANDIDATES=0.
EVENT_DIRECTION_ATTESTATIONS=0. BOUND_EVENT_POPULATION=0.
P0_ELIGIBLE_OPPORTUNITIES=0. P0_REAL_PROSPECTIVE_PATH=NO.
METRICS_REAL_READY=NO. REGIME_REAL_READY=NO. MECHANICS_REAL_READY=NO.
EXPERIMENT_51_READY=FALSE. EXPERIMENT_51_EXECUTED=NO.
DISCOVERY_ACTIVATED=NO. POLICY_WINNER=NONE. EDGE=NOT_DEMONSTRATED.

Remaining scientific gates: future legitimate release, explicit human semantic
admission and attestation before its cutoff, authenticated causal Price binding,
81H/derived inputs, future separately authorized DISCOVERY phase and population.
No fake Event, retrospective relabel, outcome inspection or holdout access.
Operational success: qualified collector is armed and waiting for reality.
