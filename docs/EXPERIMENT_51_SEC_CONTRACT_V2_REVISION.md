# Experiment 51 — SEC contract V2 revision (append-only supersession)

Status: **V2 ACTIVE IN THE JOURNAL — RUNTIME DEPLOYMENT PENDING**
Date: 2026-10-15
Branch: `manual/51-sec-user-agent-revision-20261015`
Base: `156784ff4fe3a756c1b60df7cde50436249245ee`
Final User-Agent: `OMA-CORE/51-Event-Discovery-v1 (prospective research; contact: mazonmalda@gmail.com)`
Active contract hash (V2): `1260c5ed85f27bfdcc7267d67dedd328f2f56675c9e1e1e1e71360a8e2139efd`
Supersession record: `112c3bd9eb655a18bd2b607d2604cabc98d843de0a14f6004105a55985cdb83f` (2026-10-15T21:47:41.998969+00:00)

## 1. Proven root cause

The SEC document inside the discovery scope returned **HTTP 403 (Forbidden, AkamaiGHost)** while the
RSS feed returned 200. Reproduced read-only with the production User-Agent, timeout and
redirect policy, with a control on the same URL:

| Request | User-Agent | HTTP | Server |
|---|---|---|---|
| RSS feed | production V1 | 200 | nginx |
| Document | production V1 | 403 | AkamaiGHost |
| Document | browser-like, no contact | 403 | AkamaiGHost |
| Document | research UA **with a contact** | 200 | nginx |

No redirect, no scope rejection, parser never reached. `document_failure.status = HTTP_FAILURE`
in the live journal matches `HTTPError` in `_failure()`. Root cause: `HTTP_FORBIDDEN` caused by a
User-Agent without contact information. The only change authorised here is that User-Agent.

## 2. Why continuation needed a new mechanism

The frozen model could not continue an existing authority:

* `SourceDiscoveryAuthorityV1.__init__` required `config['contract'] == CONTRACT` exactly, so any
  revision broke reading of the historical state;
* `activate()` requires a virgin root **and** a virgin source journal (`source journal already
  exists; no mixing histories`), so a normal re-activation would have produced a **new baseline**
  and a **new `first_seen`** for the already-discovered document;
* the source journal holds a `discovery_binding` pointing at the original `authority_id`, and
  `_capture` / `verify_receipt_proof` compared it by identity.

Therefore: no re-activation. Revision happens **inside the existing journal, append-only**.

## 3. Design (additive only)

New symbols in `core/scientific/event_discovery.py`:

| Symbol | Meaning |
|---|---|
| `CONTRACT` / `CONTRACT_HASH` | **unchanged** (`831c49f0…`); V1 stays frozen and authoritative for history |
| `CONTRACT_V2` | `dict(CONTRACT, user_agent=USER_AGENT_V2)` — hashes to `1260c5ed…39efd` |
| `CONTACT_APPROVED` / `USER_AGENT_V2` | owner-authorised public contact and the frozen final User-Agent |
| `CONTRACT_V2_HASH` | digest of V2 |
| `CONTRACT_CHAIN` | `{V1_HASH: CONTRACT, V2_HASH: CONTRACT_V2}` — the only admissible contracts |
| `SUPERSESSION_KIND` | journal record kind `authority_supersession` |
| `REVISION_REASON` | `SEC_HTTP_403_CONTACT_USER_AGENT` |
| `supersession_record(...)` | builds (never writes) `previous_authority_id`, `previous_contract_hash`, `supersedes_authority_id`, `contract`, `contract_hash`, `reason` |
| `SourceDiscoveryAuthorityV1.supersede(root, ...)` | appends one revision record under the poll lock; refuses unknown contracts, duplicate revisions and concurrent revision |

Behaviour changes, all fail-closed:

* `__init__` accepts any contract in `CONTRACT_CHAIN` and validates the supersession chain
  (`previous_authority_id` / `previous_contract_hash` must chain from the active authority).
* `authority_id` remains the **original** activation digest; `active_authority_id`,
  `active_contract_hash`, `active_contract`, `authority_ids` and `supersessions` are exposed.
* Source-journal bindings and receipt proofs are accepted when `authority_id` belongs to
  `authority_ids` (historical proofs keep verifying).
* `_fetch(url, *, feed, user_agent=None)` uses the active contract's User-Agent; the default keeps
  V1 behaviour for direct callers.
* `poll()` revalidates the authority and performs feed and document requests with the **active**
  contract's User-Agent.
* `status()` keeps `contract_hash = CONTRACT_HASH` (historical identity) and adds
  `active_contract_hash`, `active_authority_id`, `contract_revisions`, `supersedes_authority_id`.

Untouched: endpoint, scope, host, document prefix, timeout (20 s), max bytes (4 MiB),
`redirects='reject-all'`, parser (`rss2-stdlib-strict-v1`), polling semantics, `PILOT` role,
one-request-per-invocation, baseline rule, receipt/admission semantics and every historical record.

## 4. Continuation semantics (no rebaseline)

* baseline row is never rewritten → `baseline_count = 25`, `baseline_hash = a58047c2…78ec`;
* the existing `discovery` row is never rewritten → `discovery_id = bf5ed0f5…bfc7`;
* `first_seen_at = 2026-10-14T15:27:14.662772+00:00` is immutable;
* all `document_failure` rows stay in place (append-only journal with a verified hash chain);
* baseline items remain non-prospective forever (excluded by GUID/link);
* a later successful retrieval records `received_at` = the real receive time of that fetch and
  `available_at` = the real time of its durable `ready` marker. RSS `pubDate`, `first_seen` and the
  historical failure times are never used as availability. No backdating is possible.

Chronology that must not collapse:

```
RSS published  <  first_seen (V1)  <  historical failures  <  revision activation
               <  later successful retrieval  <  durable receipt/publication
```

## 5. Qualification

Run from a MEDIUM context with a clean temporary directory (the shared venv interpreter is
LOW-labelled and cannot use the default temp directory):

```powershell
$env:TMP=$env:TEMP='C:\Users\KiTO\AppData\Local\Temp\oma-pytest'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='C:\Users\KiTO\Documents\OMA-CORE\.venv\Lib\site-packages'
C:\Users\KiTO\AppData\Local\Python\pythoncore-3.11-64\python.exe -m pytest `
  tests/test_event_discovery_revision.py tests/test_event_discovery.py tests/test_real_event_receipt.py `
  -q -p no:cacheprovider --basetemp="$env:TMP\bt"
```

Observed with the FINAL User-Agent: `35 passed` (revision suite), `47 passed` (existing SEC suite),
`28 passed` (receipts); `git diff --check` clean. The final User-Agent was additionally validated
over the network **before** activation with the production timeout and redirect policy: document
`200 OK` (nginx, `text/html`) and feed `200 OK` (`application/rss+xml`), no `Location` header.
Preservation was verified **read-only against the live journal** before and after activation:
frozen `authority_id`, `baseline_hash`, `discovery_id`, `first_seen` all match, contract V1 still
admitted by the chain, and the historical failure rows untouched.

Test coverage of the required properties: old hash unchanged, new hash differs, User-Agent the only
behavioural difference, no new baseline, identical `discovery_id`, identical `first_seen`, untouched
historical failures, real later receive/availability times, no backdating, baseline items remain
non-prospective, redirects still rejected, off-scope still rejected, parser semantics unchanged,
no automatic EventDirection, no automatic P0, plus supersession cannot mutate the old authority,
duplicate a discovery, recreate a baseline or delete a failure.

## 6. Activation — applied (append-only), runtime deployment pending

Applied on 2026-10-15T21:47:41.998969+00:00 with the owner-approved contact frozen in V2:

```
ROOT_AUTHORITY_ID         = 911c62049403922a473c28438bc0825594243fa498543770ed16e0f85ca87ac2
SUPERSESSION_RECORD_ID    = 112c3bd9eb655a18bd2b607d2604cabc98d843de0a14f6004105a55985cdb83f
SUPERSESSION_ACTIVATED_AT = 2026-10-15T21:47:41.998969+00:00
ACTIVE_CONTRACT_HASH      = 1260c5ed85f27bfdcc7267d67dedd328f2f56675c9e1e1e1e71360a8e2139efd
REBASELINE_PERFORMED      = NO
```

Exactly one `authority_supersession` row was appended under the poll lock. The original authority,
baseline (25 / `a58047c2…`), the single discovery (`bf5ed0f5…`), `first_seen`, and every
`document_failure` row are unchanged. The old code path still loads the journal
(`contract_hash = 831c49f0…`), so the revision is backward-compatible for readers.

**Outstanding operational step (not authorised in this cut):** the scheduled SEC task executes
`OMA-CORE-RUNTIME-SEC51`, whose worktree is at `6a9bdca` and therefore still contains the **pre-V2**
module (`A06EEEC0…`). Until that runtime carries the V2 code, its natural polls keep using the V1
User-Agent; the supersession only takes effect once the runtime is deployed from this branch. That
deployment is a runtime change and requires explicit owner authorisation.

```python
# applied once, from an authorised operator context:
from core.scientific.event_discovery import SourceDiscoveryAuthorityV1
SourceDiscoveryAuthorityV1.supersede(r'<state root>')
```

`supersede()` appends exactly one record, keeps the original authority auditable, and never
rebaselines. After deployment, the next **natural** scheduled poll is the first one to use V2; the
poller must not be invoked manually.

## 7. Follow-ups (not part of this cut)

* `SEC_POLL_GUARD_FOLLOWUP_REQUIRED=YES`: the scheduler interval (~300 s) and the poll guard
  (`>= 300 s` since the previous attempt) combine with trigger jitter so roughly every second
  invocation raises `next normal 5-minute poll required`. This is unrelated to the 403 and gets its
  own operational cut.
* EventDirection remains manual (human attestation); no P0 opportunity is created automatically.
