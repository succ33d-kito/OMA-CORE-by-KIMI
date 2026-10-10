# STEP 48F: explicit public transport

Starting commit: 39c249ff61308535fafc0a35c25a133a084a5079.

CONTRACT_MISMATCH: Requests prepares query parameters into the request URL;
HTTPAdapter.build_response assigns that full URL to response.url. STEP 48E
compared it to the bare endpoint. This was reproduced by preparing a request
and reading installed Requests code, without network activity.

The narrow correction authenticates the complete URL against the exact endpoint
plus `?symbol=BTCUSDT&period=5m&limit=5`. No query stripping, permissive URL
normalization, alternate host, redirect or parameter substitution is permitted.
The transport returns the observed URL unchanged. Fixture transports now return
that same full URL. No scientific timing, payload normalization or raw commitment
semantics change; existing frozen design/activation/runner remain unchanged.

`public_http_transport` uses a fresh Requests Session per GET, trust_env=False,
zero default adapter retries, no auth/cert/cookies, no redirects, fixed public
endpoint/parameter whitelist, caller timeout unchanged within (0,8] seconds.
Response.content is returned without JSON decoding or reserialization. Requests
returns HTTP entity-body bytes (after library transfer/content decoding); it does
not expose TLS/wire framing. Accept-Encoding requests identity encoding.

Requests' timeout is a connect/read inactivity limit, not a hard total wall-clock
deadline. The unchanged adapter and runner enforce causal deadline rejection.
There is no claim that blocking DNS or a slowly streaming response is forcibly
terminated exactly at the slot deadline. Runtime qualification must preserve this
distinction; no late evidence may be admitted.

Qualification uses patched HTTPAdapter.send with real Requests preparation and
Session behavior, while socket connection functions are blocked. No real HTTP,
state activation, scheduler, observations_v2 or research-gate evaluation occurs.

Infrastructure only: EDGE=NOT_DEMONSTRATED, REGIME_VALIDATED=NO,
MECHANICS_VALIDATED=NO, POLICY_WINNER=NONE.
