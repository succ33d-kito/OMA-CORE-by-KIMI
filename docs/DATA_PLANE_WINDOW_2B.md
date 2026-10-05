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

## Descriptive radar v0

WorldState verifies source directories and suppresses evidence unavailable at its
cutoff. Quality reports raw span, timestamp skew and age without freshness gates.
Unknown source times stay unknown; local clock continuity is not independent NTP
accreditation. Caller-supplied representations alone are not signed evidence.

Radar thresholds must be explicit positive decimal fractions, frozen no later
than the WorldState cutoff, PILOT-only. Initial primitives: mark/index fraction,
funding-rate difference from observed median, relative spread difference from
observed median, and missing evidence. No history-dependent return primitives are
implemented. Fixed primitive order and lexicographic market cap are selection
conventions, not performance rankings. Every market retains findings and either
a candidate-subject mapping or an explicit non-candidate reason. Missing markets
can produce quality-watch candidates, never fabricated prices.

Config timestamps are contractual assertions; durable ex-ante registration must
be supplied by the caller before operational use. No outcome-based calibration
has been performed. Candidate status remains OBSERVED, not validated Alpha.
