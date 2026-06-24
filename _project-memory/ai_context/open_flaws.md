# Open Flaws

## FLAW-21 — Trade.close() Idempotency

| Field | Value |
|-------|-------|
| **Status** | 🔶 Open — Low Risk |
| **Affected File** | `core/schemas/trade_schema.py:92` |
| **Description** | `Trade.close()` lacks a status check. If called twice, PnL is recomputed from potentially stale prices. |
| **Risk** | LOW — no practical double-close path exists. Trade is removed from `self.positions` before close. |
| **Fix** | Add `if self.status == TradeStatus.CLOSED: return` |
| **Priority** | LOW — apply before Micro Capital |
| **Blocks Demo** | ❌ No |

---

## FLAW-24 — CrashDetector Reporting Equity Hardcoded

| Field | Value |
|-------|-------|
| **Status** | ❌ Open — Low Risk |
| **Affected File** | `core/execution/crash_detector.py:256` |
| **Description** | `summary()` calls `self.crash_mode(10000)` with hardcoded 10000 equity. Trade blocking paths use correct equity; only reporting affected. |
| **Risk** | LOW — trade safety unaffected. Reporting may show wrong crash mode when equity ≠ 10000. |
| **Fix** | Add `current_equity` parameter to `summary()`, pass actual equity from callers |
| **Priority** | MEDIUM — apply after 7-day smoke run, before Micro Capital |
| **Blocks Demo** | ❌ No |

---

## FLAW-25 — Guard Audit Attribution Improvement

| Field | Value |
|-------|-------|
| **Status** | ❌ Open |
| **Affected File** | `core/monitoring/telemetry.py` (GuardAuditRecorder) or `scripts/extended_demo_realtime.py` |
| **Description** | Guard audit records from the active smoke run have `guard_source: "Unknown"` and `block_reason: "unknown"`. The guard attribution logic does not correctly identify which guard component caused each block. 6 records with this issue observed so far. |
| **Risk** | MEDIUM — guard monitoring is partially blind. We know blocks occurred but not which guard caused them. |
| **Evidence** | `_extended_demo/guard_audit_20260623_222729.jsonl` — all 6 entries have Unknown/unknown |
| **Priority** | HIGH — blocks observability of guard behavior |
| **Blocks Demo** | ⚠️ CONDITIONAL — gate requires "every anomaly classified and logged" |

---
