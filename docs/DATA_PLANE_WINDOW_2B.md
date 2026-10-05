# Repository readiness, separate from local operational verification

LOCAL_RUNTIME_STATUS = UNVERIFIED. No live deployment, slot inference or manual
replacement capture is part of this window. Existing local processes must be
verified/restarted separately to load new code.

## Multi-market premium

`multi_market_premium.capture_premium_cycle` retains one complete official
premiumIndex array, projects only the frozen five-market PILOT universe, persists
before availability and rejects unknown fields. Mark/index/funding, next funding
time, source time and full raw provenance are retained. Funding is a rate
observation, not a payment. Missing symbols remain missing.

The [official market-data API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
supports premiumIndex without a symbol (array response).
20 focal tests passed (8 premium, 12 capture).
REAL_CAPTURE_PENDING_LOCAL_VERIFICATION: no real HTTP capture attempted here.

Edge/Regime/Mechanics validation = NO. Policy winner = NONE.
