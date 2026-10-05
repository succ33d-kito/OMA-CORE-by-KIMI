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

## H1 collector checkpoint

`python -B -m core.scientific.multi_market_collector --state "C:/Users/KiTO/Documents/O-C data/prospective/multi-market/h1-state" --universe "C:/Users/KiTO/Documents/O-C data/prospective/multi-market/universe-v0"`

The runner holds a Windows process lock, verifies sealed configuration and prior
attempts on restart, and targets the next UTC hour +5 seconds. No catch-up occurs.
Each slot has an exclusive attempt directory; completed, failed, missed and
interrupted slots cannot be overwritten or retried. Raw errors stop the process;
restarting verifies history and resumes at the next future slot. This foreground
command can also be launched hidden with Start-Process. No scheduled-task/admin
changes, automatic login restart or prevention of Windows suspension is claimed.

Startup verification: runner PID 8736 (launcher 16716), lock held, integrity PASS;
next target 2026-10-05T01:00:05Z. Zero official H1 cycles at startup. Logs are in
`O-C data/prospective/multi-market/runner-logs`. Health reports last verified state,
not proof of current process liveness; verify PID and lock separately.

One diagnostic TLS handshake timed out before a response. A separate second
attempt produced a COMPLETE five-member DIAGNOSTIC cycle, reopened successfully:
`d9e87b0d15312ade4b5cc111c6e0df8a41ce0e729352ab135a73bd456c16cd10`.
Start 2026-10-05T00:02:16.853953Z; reception 00:03:39.229277Z;
availability 00:03:39.249423Z. Capture span 82.39547 seconds; this is not
simultaneous or a low-latency quote certification. Directory:
`O-C data/prospective/multi-market/diagnostics/startup-2026-10-05-after-tls-timeout`.
No diagnostic cycle enters official H1 population. The earlier failed directory
remains untouched. Collector + capture validation: 18 focal tests passed.

## Universe snapshot v0

`universe_snapshot.load_snapshot(cycle_directory, universe_directory, as_of=...)`
returns an immutable causal view backed only by verified persisted evidence.
Before cycle availability it exposes neither member values, cycle identity nor
future missingness. At/after availability, each symbol is AVAILABLE with its
evidence or MISSING without imputation. The universe itself must already be frozen
at the cutoff. DIAGNOSTIC remains explicitly distinct from H1. No rankings,
signals or outcomes are introduced. Four snapshot tests plus twelve capture tests
pass; compile/diff checks pass. This is a data view, not a trading World State engine.
