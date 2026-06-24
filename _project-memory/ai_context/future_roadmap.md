# Future Roadmap

## Phase 1 — Operational Validation (2026-06) ✅ COMPLETE

**Status:** All tasks complete, smoke run active.

**Success criteria:**
- [x] 281 tests reconciled
- [x] Architecture mapped
- [x] Execution blocks explainable
- [x] Guard blocks explainable
- [x] Health status documented
- [x] Extended Demo preflight = GO

---

## Phase 2 — 30-Day Validation (2026-07) ⏳ PENDING

**Status:** Waiting for 7-day smoke run to complete.

**Success criteria:**
- [ ] Smoke run completes with 0 NO-GO triggers
- [ ] All 17 Extended Demo Gate criteria pass
- [ ] Daily/weekly reports generated
- [ ] Regression suite passes at t=15d and t=30d
- [ ] Gate verdict published

---

## Phase 3 — System Consolidation (2026-07) ⏳ PENDING

**Status:** Waiting for 30-day validation.

**Success criteria:**
- [ ] FLAW-25 fixed (guard audit attribution)
- [ ] FLAW-24 fixed (crash detector reporting equity)
- [ ] FLAW-21 fixed (Trade.close idempotency)
- [ ] All open flaws reviewed and either fixed or deferred
- [ ] Signal quality re-audited on real market data

---

## Phase 4 — Opportunity Layer V1 (FUTURE) 📋 NOT STARTED

**Status:** Concept only — do not implement yet.

**Description:** Transform pipeline from `Event → Agent → TradeSignal → PaperTrading` to `Event → Opportunity → User Profile → Action`. The Opportunity Layer adds scored, typed, risk-weighted abstractions between events and actions.

**Note:** This is the future product direction of O.M.A.-C.O.R.E. beyond the current OSIRIS trading system. Do not implement during operational validation phases.

---

## Phase 5 — User Profiles (FUTURE) 📋 NOT STARTED

**Status:** Concept only — do not implement yet.

**Description:** Three persona models (Trader, Entrepreneur, Creator) that evaluate the same opportunity from different perspectives and produce different actions. MetaCouncil prototype already exists.

---

## Phase 6 — OSIRIS Dashboard (FUTURE) 📋 NOT STARTED

**Status:** Concept only — do not implement yet.

**Description:** A web dashboard to monitor OSIRIS performance, guard activity, telemetry, and trade history.

---

## Phase 7 — Micro Capital Validation (FUTURE) 🚫 NO-GO

**Status:** Blocked until Phases 1-2 complete.

**Success criteria:**
- [ ] Extended Demo Gate verdict = GO
- [ ] FLAW-24 fixed
- [ ] FLAW-21 fixed
- [ ] Signal quality >55% (real market data)
- [ ] Small real funds deployed for 30+ days

---

## Phase 8 — Real Capital Validation (FUTURE) 🚫 NO-GO

**Status:** Blocked until Phase 7 complete.

**Success criteria:**
- [ ] Micro Capital completes 30+ days with acceptable risk
- [ ] Full capital deployed
- [ ] Performance evaluation against benchmarks
