# 50B causal descriptive Mechanics integration

`build_causal_mechanics` loads an explicit-role causal raw snapshot and reuses
LatentMarketContext's exact Funding/GlobalPositioning mappings. Optional Regime
must identify an exact persisted, reconstructed, same-role causal Regime v2.
`append_causal_mechanics` persists the versioned representation and exact raw,
attestation and derived dependency IDs. No evidence means no persisted derivative.
Validation reconstructs both payload and identity; Metrics retain their specialized
bundle gate rather than being forced through the generic raw-observation gate.

Supported facts: closed OHLCV, published funding rate, OI levels/OI value and
provider positioning/taker ratios, when their existing role/causal gates pass.
Regime dependency retains the existing full MarketState, including price return,
volume ratio, range and volatility. Each raw value retains source ID, source
metric time and availability. Missing role-compatible features remain missing;
unsupported dimensions are explicit null, never neutral values.

Not derived: OI change from a level, aggressor imbalance from taker ratio,
trade intensity/average trade size without admitted trade data, resting liquidity,
absorption, participant identity/intent, capital flow or realized funding payment.
The historical aggTrades reducer has no admitted historical availability and is
not consumed. Participation's trade-count inputs are absent from the price
contract. The separate context classifier's degenerate neutral fallbacks are not
used to manufacture known dimensions.

This is descriptive infrastructure, not full participant mechanics or prediction.
The Mechanics v2.1 historical exclusion freeze and MM hypothesis blocks remain
unchanged. No Knowledge/Criterion, policy decision or outcome integration is added.
