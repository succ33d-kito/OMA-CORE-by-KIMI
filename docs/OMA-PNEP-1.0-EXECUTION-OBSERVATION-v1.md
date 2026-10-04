# Execution Observation Contract v1

Baseline: `b14de8ee1a55f73664c0af7ae486264bd3f06467`.

## Evidence, not a cost model

ExecutionObservation represents BTCUSDT / Binance USDⓈ-M / linear perpetual at an
explicit decision time and DatasetRole. It requires no ActionIntent. No collector,
network request, fill, order, estimate, execution result or cost total is included.

ExecutionReceipt is an immutable reference to an upstream capture: exact endpoint,
receipt ID, provenance SHA-256, raw JSON response, role, request start, receipt time,
availability and (for fees) explicit account reference. Strict response projection
supports three source contracts:

- bookTicker: bid/ask; quantities retained only as raw response evidence, no depth engine.
- premiumIndex: mark/index and latest funding-rate observation; not a realized payment.
- commissionRate: account-specific maker/taker rates; not a generic public fee assumption.

Only BTCUSDT object responses are accepted. Unknown fields, duplicate JSON keys,
wrong endpoints, crossed books and invalid numerical representations fail closed.
Response schemas are grounded in official documentation:
[market data](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
and [user commission rate](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/account#user-commission-rate).

## Causality and UNKNOWN

Each source has its own receipt/availability timestamps; no shared timestamp is
invented across independent responses. All provided local timestamps must be UTC.
Request start cannot follow receipt; receipt cannot follow availability. An exchange
timestamp, when present, cannot follow receipt and never substitutes for it.

At decision time, unknown receipt/availability produces UNKNOWN; later availability
produces LATE. Missing source/field/null produces UNKNOWN. `value(measure)` returns
None unless the corresponding evidence is VALID at that cut. No interpolation,
retrospective availability, historical averages or default rate is used. An actual
observed zero remains distinct from UNKNOWN.

`time` is the provider timestamp in epoch milliseconds (book transaction time or
premium-index snapshot time). `nextFundingTime` is a schedule, not proof of a future
rate or payment. No funding interval/payment calculation is inferred. Fee responses
have no fabricated exchange timestamp. Request/receipt timing is preserved, not
reported as one-way network latency. No freshness/maximum-age policy is invented.

## Units and separation

Measures name their units explicitly: prices, mid and absolute spread are USDT per
BTC; funding and commission rates are decimal fractions. 0.001 = 0.1% = 10 bps;
the API does not accept percent/bps strings or automatically convert them.
Rates must be finite decimal strings in [-1,1]; negative values remain signed.
Numerical strings are canonicalized deterministically, with bounded precision.

Mid = (bid + ask)/2 and spread = ask - bid, only from the same causal book receipt.
Fixed sufficient Decimal precision prevents ambient context from changing these
derivations. No relative spread is emitted. Slippage is always NOT_OBSERVED (None).
There is no fill adjustment, fee charge, funding payment or total_cost, so this
contract cannot double-charge spread. Future models must choose their own single
accounting location for spread; this observation does not decide that location.

## Reuse and legacy findings

Reuse: PNEP roles/statuses/UTC/digest and existing Decimal canonicalization.
The current prospective receipt gate only admits raw Price/OHLCV; other raw
features have unknown availability. It is not silently extended for this slice.
Price capture preserves request/server/receipt timing and has separate clock
checks; those are not evidence of book depth, fees, funding or execution latency.

DO_NOT_USE as observations: SlippageEngine defaults and simulated fill prices.
`slippage_pct` is divided by 100 (percent), while `get_spread_pct` returns bps/10000
(fraction despite its name). The code applies that spread fraction to each fill.
Additionally, `configured_spread or default` discards an explicit zero spread.
These are relevant legacy semantics/risks, not fixes in this slice. No downstream
double-count bug is asserted without inspecting its callers. No legacy module is
changed or imported by this contract.

## Trust boundary, tests and next action

This is a representation/validation contract, not authenticated capture. A caller
can fabricate response strings, receipt IDs or provenance hashes; structural checks
do not prove that HTTP happened or that a rate was factual. A future trusted capture
adapter must verify those references and prohibit modeled/scenario evidence. There
is no convenience API for 5-bps assumptions, but deliberate forged evidence cannot
be identified by this contract alone.

No live execution-condition receipts were inspected or captured in this slice.
Fixtures demonstrate schema adaptation only. Bid/ask, depth, current funding and
account fees therefore remain empirically unverified here, not claimed observed.
Identity commits canonical payloads, provenance, role and timestamps independent
of JSON/receipt order and process hash seed. Inputs and outputs are immutable;
parsing returns fresh data and cannot mutate the stored observation.

Next minimum: one prospective top-of-book capture with persisted receipt and
verified availability, then adaptation to this contract; no execution or cost model.

Edge = NO. Regime validation = NO. Mechanics validation = NO. Policy winner = NONE.
