# Current Priorities

## Priority 1 — 7-Day Smoke Run (ACTIVE)

**Status:** RUNNING (cycle 3 of ~672, started 2026-06-23 22:27 UTC)

The smoke run is the first stage of Extended Demo operational validation. It runs for 7 days with 15-minute cycle intervals. All monitoring, telemetry, audit, and health checks are active. If the smoke run completes without NO-GO triggers, proceed to the 30-day validation.

**Success criteria:** 0 NO-GO triggers, all 17 Extended Demo Gate criteria pass.

---

## Priority 2 — 30-Day Validation (PENDING)

**Status:** ⏳ Waiting for smoke run completion

The 30-day validation run is the second stage. Longer duration tests operational stability under varying market conditions. Uses 1-hour cycle intervals.

**Success criteria:** Complete 30 days with 0 NO-GO triggers, pass gate review.

---

## Priority 3 — FLAW-25 (OPEN)

**Status:** ❌ Open — discovered during smoke run

Guard audit records show `guard_source: "Unknown"` and `block_reason: "unknown"` for all 6 guard blocks observed during the smoke run. The guard audit attribution logic needs improvement to correctly identify which guard component caused each block.

**Success criteria:** All guard audit records have accurate `guard_source` and `block_reason`.

---

## Priority 4 — FLAW-24 (OPEN, LOW RISK)

**Status:** ❌ Open — non-blocking for smoke run

`crash_detector.summary()` hardcodes equity at 10000 instead of using actual equity. Trade safety is unaffected (all blocking paths use correct equity), but reporting is wrong when equity ≠ 10000.

**Fix plan:** Add `current_equity` parameter to `summary()`, update callers.

---

## Priority 5 — FLAW-21 (OPEN, LOW RISK)

**Status:** 🔶 Partially addressed — defense-in-depth needed

`Trade.close()` lacks an idempotency guard. No practical double-close path currently exists (trade is removed from positions list before close), but adding a status check is good practice.

**Fix plan:** Add `if self.status == CLOSED: return` to `Trade.close()`.

---

## Priority 6 — Opportunity Layer V1 (FUTURE)

**Status:** 📋 Not started — concept only

The future product direction transforms the pipeline from `Event → TradeSignal → PaperTrading` to `Event → Opportunity → User Profile → Action`. The Opportunity Layer would add scored, typed, risk-weighted abstractions between events and actions.

**Note:** Do NOT implement yet. This is architectural awareness only.

---

## Priority 7 — Trader Profile (FUTURE)

**Status:** 📋 Not started — concept only

The Trader user profile is one of three personas (Trader, Entrepreneur, Creator) that O.M.A.-C.O.R.E. will eventually serve. MetaCouncil already evaluates opinions for three profiles.

---

## Priority 8 — Creator Profile (FUTURE)

**Status:** 📋 Not started — concept only

Content creation persona. Not yet implemented.

---

## Priority 9 — Founder Profile (FUTURE)

**Status:** 📋 Not started — concept only

Entrepreneur/business persona. Not yet implemented.

---

## Priority 10 — OSIRIS Dashboard (FUTURE)

**Status:** 📋 Not started — concept only

A future web dashboard for monitoring OSIRIS performance, guard activity, and trade history. Not yet implemented.
