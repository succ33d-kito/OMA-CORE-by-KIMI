# Prospective premiumIndex observation

`premium_index_capture.capture_premium(new_directory)` performs one fixed
BTCUSDT USD-M PILOT HTTP request. Raw and metadata are exclusively persisted and
fsynced, validated, then availability is sampled internally and committed.
`load_premium` verifies commitments without factual overrides or recovery.
Unknown wire fields fail closed. This isolated adapter follows the book capture
pattern without changing the Price or Event ledgers.

`lastFundingRate` is an observed decimal fraction, not a realized payment.
`nextFundingTime` is provider schedule metadata, never availability. Full raw
fields remain preserved, including estimated settlement, interest and exchange time.
No funding costs, fills, fees, slippage estimates or total costs are computed.

Validation: 11 adapter + 34 ExecutionObservation tests, 45 passed; compile/diff PASS.
One real request on 2026-10-04 23:53 UTC (October 5 local) succeeded and reopened:
receipt `900e841921ce62e54f4e2c29d432e02ce33f9b470a72d76abb4f9d2b3f0e4c34`.
Request 23:53:15.069411Z, received 23:53:16.773862Z, available 23:53:16.795801Z.
External data: `O-C data/prospective/execution/first-premium-index-2026-10-05`.
Local custody and trusted local clock are required; hashes are not signatures.
Edge/Regime/Mechanics validation: NO. Policy winner: NONE.
