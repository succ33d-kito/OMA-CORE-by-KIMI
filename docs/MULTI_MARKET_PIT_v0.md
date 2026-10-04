# Frozen multi-market PILOT data plane

Universe v0 is BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT and BNBUSDT, sorted canonically;
Binance USD-M linear USDT perpetuals. `freeze_universe` verifies TRADING,
PERPETUAL, USDT quote/margin in a persisted official exchangeInfo response before
creating the immutable universe commitment. No outcome-based selection occurs.

Verified 2026-10-04T23:57:27.227981Z:
`079123ad974947276cc3a21850b7c3375e1f41b13d09e5b71efc4787a08a4623`.
External path: `O-C data/prospective/multi-market/universe-v0`.

One all-symbol bookTicker response is retained in full; only frozen members are
projected. The [official endpoint contract](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
supports omitting symbol to receive an array. This is SINGLE_HTTP_NOT_SIMULTANEOUS:
members may have different exchange timestamps. Capture span is local start to
availability, not a guarantee about exchange timestamp skew or quote freshness.

Members retain raw commitment, exact wire fields, update IDs, exchange/reception/
availability times and immutable projection identities. Unknown wire fields reject
the cycle. Missing members produce INCOMPLETE without last-value fill. Cycle IDs
bind universe, kind and slot; projection IDs additionally bind raw and metadata.

H1 requests can begin only during the first two minutes of the current slot;
DIAGNOSTIC is separate. Neither can replay historical data as live. Exclusive
directories prevent overwrite. A missing completion marker cannot be finalized
retrospectively. Hash verification requires trusted local custody and clock; it
does not protect against deliberate complete rehashing by a privileged attacker.

12 focal tests pass, compile and diff checks pass. ExchangeInfo verification was
real; no real multi-market book cycle has yet been captured at this checkpoint.
No Price/Event ledger changes. No outcomes, signals, fills or costs.
Edge/Regime/Mechanics validation: NO. Policy winner: NONE.
