# One-shot bookTicker capture adapter

Baseline: `e98da41f82b0b49c9fccaa84d4a2cd06075b8e96`.

`capture_book(new_directory)` performs one official BTCUSDT USD-M bookTicker
request with no redirects, retries or caller-supplied prices/timestamps. The scope
is fixed to BTCUSDT / Binance USDⓈ-M / linear perpetual / PILOT.

Raw bytes and canonical receipt metadata are written exclusively and fsynced
before validation. A ready marker is created only after successful projection;
its availability timestamp is assigned internally after persistence. An incomplete
or invalid capture stays without availability. Existing directories cannot be
overwritten through the capture API.

`load_book(directory, decision_at=...)` validates persisted content, metadata and
availability commitments and projects through ExecutionObservation. It accepts no
bid/ask/receipt/availability overrides. The default decision cut is availability,
solely for structural validation, not a claimed trading decision. Clock continuity
uses the existing primitive; no server-time request or clock correction is made.
Request duration is not one-way latency or execution latency.

The hashes detect ordinary raw/metadata substitutions; unrestricted external file
rewrites with complete recomputation, clock compromise or hostile Python remain
outside this local API boundary. This is not a signed receipt authority.

## Real test, 2026-10-04 UTC

Exactly one market request was made to:
`https://fapi.binance.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT`.
The response was HTTP 200, application/json, 150 bytes; raw and receipt metadata
were preserved outside Git under `O-C data/prospective/execution/first-book-ticker-2026-10-04`.

Projection failed with `wrong symbol or unsupported response fields`. The actual
symbol was correct. The response additionally contained `lastUpdateId`, absent
from ExecutionObservation v1's book field allowlist. The field was not stripped,
no upstream contract was modified and no second capture was made. No ready marker
or causal ExecutionObservation was produced; availability remains UNKNOWN.

That first response remains NON-CAUSAL, available_at UNKNOWN, permanently outside
the successful projection path. No recovery/finalize API exists.

## Prospective validation, 2026-10-04 23:50 UTC (October 5 local)

`lastUpdateId` is now explicitly preserved as nonnegative integer exchange update
metadata (`source_update_id`), included in payload/evidence identity. It is not a
timestamp, trade identifier or latency. No sequence continuity is inferred.
Unknown wire fields still fail closed. Availability is sampled internally only
after raw/metadata fsync and successful validation; the marker must persist before
return. Caller-supplied factual values remain forbidden by the capture API.

One sandbox connection was denied before HTTP reception. One subsequent authorized
HTTP request succeeded, with no retry after response:

- Receipt: `d0a33ce448d41ad909eecb102b1d4721e35a28aed85282571da8fb7b27c7a2e9`.
- Raw SHA256: `70c84a1f5a8936ce951c6e8b29746367ae6b77611e6229c2047d944f00bbb3fb`.
- Update ID: `11735124376559`; exchange time: `2026-10-04T23:50:34.547Z`.
- Request: `23:50:34.410148Z`; received: `23:50:35.910445Z`;
  available: `23:50:35.926758Z`, all October 4 UTC.
- Bid/ask: 86485.00 / 86485.10 USDT/BTC; mid 86485.05; absolute spread 0.10.
- Reopen, commitments and causal order: PASS. Fees/funding UNKNOWN; slippage NOT_OBSERVED.
- External directory: `O-C data/prospective/execution/second-book-ticker-2026-10-05-network-authorized`.

Verdict: REAL_EXECUTION_PIT_OBSERVED. No recurring collector was started here.

## Validation

21 adapter tests plus 34 ExecutionObservation tests pass (55 total), using
transport fixtures. They cover immutable/reopened receipts, raw/metadata/time
substitution, wrong scope, crossed/malformed/missing book values, no caller value
overrides, source separation and UNKNOWN non-book measures. Initial tests exposed
order-dependent metadata hashing; canonical hashing fixed reopening identity.

No Event/Price ledger, trading code, fees, funding or outcomes were touched.
No fill, relative spread, cost model or total cost is produced.
Edge = NO. Regime validation = NO. Mechanics validation = NO. Policy winner = NONE.
