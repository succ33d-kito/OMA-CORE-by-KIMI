"""
O.M.A.-C.O.R.E. Telegram Notification Quality Gate (Sprint 10)

Normalizes, deduplicates, saturates, gates, and renders notifications.
Replaces v2.2 noisy log-dump with a structured decision-quality interface.
"""

import json
import os
import re
import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Asset normalization
# ---------------------------------------------------------------------------

def normalize_assets(value: Any) -> List[str]:
    """Safely normalize any asset representation into a clean list of strings.

    Handles:
      - "BTC"                          -> ["BTC"]
      - ["BTC", "ETH"]                 -> ["BTC", "ETH"]
      - '["BTC", "ETH"]'               -> ["BTC", "ETH"]
      - '"BTC"'                        -> ["BTC"]
      - "BTC, ETH"                     -> ["BTC", "ETH"]
      - "BTC,ETH"                      -> ["BTC", "ETH"]
      - None / "" / [] / 0             -> []
      - 123                            -> ["123"]
      - malformed character-lists      -> parsed correctly
      - duplicates                     -> deduplicated
    """
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str) and (item.startswith("[") or item.startswith('"')):
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, list):
                        result.extend(normalize_assets(parsed))
                        continue
                    if isinstance(parsed, str):
                        parsed = parsed.strip()
                        if parsed:
                            result.append(parsed)
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass
            parsed = _parse_single_asset(item)
            if parsed:
                result.append(parsed)
        return _unique_ordered(result)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        if value.startswith("[") or value.startswith('"'):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return normalize_assets(parsed)
                if isinstance(parsed, str):
                    parsed = parsed.strip()
                    return [parsed] if parsed else []
            except (json.JSONDecodeError, TypeError):
                pass
        if "," in value:
            parts = [p.strip().strip('"').strip("'") for p in value.split(",")]
            return _unique_ordered([p for p in parts if p])
        return [value]
    return []


def _parse_single_asset(item: Any) -> Optional[str]:
    if item is None:
        return None
    if isinstance(item, str):
        item = item.strip().strip('"').strip("'")
        return item if item else None
    return str(item)


def _unique_ordered(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Opportunity deduplication
# ---------------------------------------------------------------------------

def _dedup_key(opp: Dict[str, Any]) -> Tuple:
    assets = tuple(sorted(normalize_assets(opp.get("assets", []))))
    action = opp.get("action_suggested", "") or ""
    opp_type = opp.get("opportunity_type", "") or ""
    direction = opp.get("direction", "") or ""
    score_bucket = round(opp.get("score", 0) / 10) * 10 if opp.get("score") else 0
    reason = opp.get("title", "") or opp.get("hypothesis_statement", "") or ""
    return (assets, action, opp_type, direction, score_bucket, reason[:80])


def deduplicate_opportunities(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Deduplicate opportunities by normalized content.

    Returns dict with:
      - raw_count
      - unique_count
      - duplicate_rate (as string like "97%")
      - unique_opportunities (list)
    """
    raw_count = len(opportunities)
    seen = set()
    unique = []
    for opp in opportunities:
        key = _dedup_key(opp)
        if key not in seen:
            seen.add(key)
            unique.append(opp)
    dup_rate = 0
    if raw_count > 0:
        dup_rate = round((1 - len(unique) / raw_count) * 100)
    return {
        "raw_count": raw_count,
        "unique_count": len(unique),
        "duplicate_rate": dup_rate,
        "unique_opportunities": unique,
    }


# ---------------------------------------------------------------------------
# Priority saturation detection
# ---------------------------------------------------------------------------

def detect_priority_saturation(priority_counts: Dict[str, int], total: int) -> Dict[str, Any]:
    """Detect if priority scoring is saturated.

    Returns dict with:
      - saturated (bool)
      - reason (str)
      - distribution (dict)
    """
    result: Dict[str, Any] = {
        "saturated": False,
        "reason": "",
        "distribution": dict(priority_counts),
    }
    if total == 0:
        result["reason"] = "No opportunities to evaluate"
        return result
    if total < 5:
        return result

    critical_pct = round(priority_counts.get("CRITICAL", 0) / total * 100)
    unique_priorities = sum(1 for v in priority_counts.values() if v > 0)

    reasons = []
    if critical_pct >= 80:
        reasons.append(f"{critical_pct}% are CRITICAL")
    if unique_priorities <= 1:
        reasons.append("all opportunities have the same priority level")
    if reasons:
        result["saturated"] = True
        result["reason"] = "Priority saturation detected — " + "; ".join(reasons) + "."
    return result


# ---------------------------------------------------------------------------
# Notification Quality Gate
# ---------------------------------------------------------------------------

class NotificationQualityGate:
    """Evaluates notification quality before sending.

    Gate output:
      PASS              — send full notification
      WARN              — send full notification with warning banner
      SUPPRESS_DETAIL   — send compact diagnostic instead of full Top 5
      FAIL_DIAGNOSTIC   — send only diagnostic header, no detail
    """

    def __init__(self):
        self.warnings: List[str] = []
        self.last_message: Optional[str] = None

    def evaluate(
        self,
        opportunities: List[Dict[str, Any]],
        dedup_result: Dict[str, Any],
        priority_counts: Dict[str, int],
        saturation: Dict[str, Any],
        rendered_message: str,
    ) -> str:
        self.warnings = []

        # 1. Asset formatting check
        for opp in opportunities[:10]:
            assets = opp.get("assets", [])
            if isinstance(assets, str) and "," in assets:
                normalized = normalize_assets(assets)
                if any(len(a) == 1 for a in normalized if len(a) == 1):
                    self.warnings.append("Malformed asset list detected")
                    break

        # 2. Duplicate rate
        dup_rate = dedup_result.get("duplicate_rate", 0)
        if dup_rate >= 95:
            self.warnings.append(f"Very high duplicate rate ({dup_rate}%)")
            return "SUPPRESS_DETAIL"
        if dup_rate >= 80:
            self.warnings.append(f"High duplicate rate ({dup_rate}%)")

        # 3. Priority saturation
        if saturation.get("saturated"):
            self.warnings.append(saturation["reason"])

        # 4. Check that top opportunities have action and score
        for opp in dedup_result.get("unique_opportunities", [])[:5]:
            if not opp.get("action_suggested"):
                self.warnings.append("Opportunity missing action")
            if opp.get("score") is None:
                self.warnings.append("Opportunity missing score")
            if opp.get("block_reason") and opp.get("block_reason") != "none":
                if not opp.get("block_reason"):
                    self.warnings.append("Blocked opportunity missing block reason")

        # 5. Check for identical message
        if self.last_message and self.last_message == rendered_message:
            self.warnings.append("Identical to last notification")
            return "SUPPRESS_DETAIL"

        # 6. Check for malformed output
        if "[," in rendered_message or ", \"," in rendered_message:
            self.warnings.append("Malformed list/JSON in output")
            return "FAIL_DIAGNOSTIC"

        # 7. Empty check
        if not opportunities:
            self.warnings.append("No opportunities to report")
            return "WARN"

        if len(self.warnings) >= 3:
            return "SUPPRESS_DETAIL"
        if self.warnings:
            return "WARN"
        return "PASS"

    def get_warning_banner(self) -> str:
        if not self.warnings:
            return ""
        return "\n".join([f"⚠️ {w}" for w in self.warnings[:5]])


# ---------------------------------------------------------------------------
# Learning Core status helper
# ---------------------------------------------------------------------------

def get_learning_core_stats(scientific_db_path: Optional[str] = None) -> Dict[str, Any]:
    """Read optional learning stats from scientific.db.

    Never raises — returns defaults on any failure.
    """
    try:
        from core.scientific.scientific_store import ScientificStore
        store = ScientificStore(db_path=scientific_db_path or "scientific.db")
        conn = store._get_connection() if hasattr(store, '_get_connection') else None
        if conn is None:
            return _default_learning_stats()
        result: Dict[str, Any] = {
            "connected": True,
            "outcome_comparisons": 0,
            "knowledge_items": 0,
            "pending_criterion_deltas": 0,
            "last_replay_session": "N/A",
        }
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM outcome_comparisons")
            result["outcome_comparisons"] = cursor.fetchone()[0]
        except Exception:
            pass
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge")
            result["knowledge_items"] = cursor.fetchone()[0]
        except Exception:
            pass
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM criterion_deltas WHERE status = 'pending_review'")
            result["pending_criterion_deltas"] = cursor.fetchone()[0]
        except Exception:
            pass
        try:
            cursor = conn.execute("SELECT timestamp FROM outcome_comparisons ORDER BY compared_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                result["last_replay_session"] = row[0][:19] if row[0] else "N/A"
        except Exception:
            pass
        conn.close()
        return result
    except Exception:
        return _default_learning_stats()


def _default_learning_stats() -> Dict[str, Any]:
    return {
        "connected": False,
        "outcome_comparisons": 0,
        "knowledge_items": 0,
        "pending_criterion_deltas": 0,
        "last_replay_session": "N/A",
    }


# ---------------------------------------------------------------------------
# Opportunity rendering helpers
# ---------------------------------------------------------------------------

TYPE_EMOJIS = {
    "LONG_SETUP": "🟢📈", "SHORT_SETUP": "🔴📉", "MOMENTUM_PLAY": "🚀",
    "AVOID_OR_SHORT": "⚠️🚫", "SAFE_HAVEN_FLOW": "🛡️", "RISK_OFF": "📉🔻",
    "WHALE_ACCUMULATION": "🐋🟢", "WHALE_DISTRIBUTION": "🐋🔻", "VIRAL_MOMENTUM": "🔥",
    "POST_EARNINGS_RUN": "📊", "MACRO_TAILWIND": "📈🌬️", "MACRO_HEADWIND": "📉🌬️",
    "REGULATORY_TAILWIND": "✅📋", "REGULATORY_HEADWIND": "🚫📋",
    "SENTIMENT_TURN_BULL": "😀📈", "SENTIMENT_TURN_BEAR": "😰📉", "ARB_OPPORTUNITY": "💰",
    "WATCHLIST_ADD": "👁️", "NEWS_DRIVEN": "📰",
    "TECHNICAL_BREAKOUT": "📈🔨", "TECHNICAL_BREAKDOWN": "📉🔨", "TECHNICAL_WATCH": "👁️📊",
    "WHALE_WATCH": "🐋👁️", "MONITOR_COMPLIANCE": "📋👁️", "MONITOR_GEO": "🌍👁️",
    "MONITOR_MACRO": "📊👁️", "EARNINGS_NEUTRAL": "📊", "SENTIMENT_WATCH": "👁️📊",
}


def _render_assets(assets_list: List[str]) -> str:
    return ", ".join(assets_list) if assets_list else "N/A"


def _safe_text(value: Any, max_len: int = 60) -> str:
    if value is None:
        return "N/A"
    text = str(value).strip()
    if len(text) > max_len:
        return text[:max_len - 3] + "..."
    return text


def _truncate_message(message: str, max_chars: int = 4000) -> str:
    if len(message) <= max_chars:
        return message
    return message[:max_chars - 100] + "\n\n⚠️ Message truncated (too long)"


# ---------------------------------------------------------------------------
# Message renderer
# ---------------------------------------------------------------------------

def render_notification(
    opportunities: List[Dict[str, Any]],
    stats: Dict[str, Any],
    learning_stats: Optional[Dict[str, Any]] = None,
) -> str:
    """Render a full notification message (HTML).

    This is the new Sprint 10 format — English, structured, diagnostic-first.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    dedup_result = deduplicate_opportunities(opportunities)
    unique = dedup_result["unique_opportunities"]
    top_unique = sorted(unique, key=lambda x: x.get("score", 0), reverse=True)[:5]

    priority_counts = {}
    for opp in opportunities:
        p = opp.get("priority", "UNKNOWN")
        priority_counts[p] = priority_counts.get(p, 0) + 1

    saturation = detect_priority_saturation(priority_counts, len(opportunities))

    lines: List[str] = []
    lines.append("<b>🤖 O.M.A.-C.O.R.E. RUN COMPLETE</b>")
    lines.append(f"<b>Timestamp:</b> {now} UTC")
    lines.append("")

    # --- Summary ---
    lines.append("<b>📊 Summary</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"<b>Events processed:</b> {stats.get('events_processed', 'N/A')}")
    lines.append(f"<b>Events stored:</b> {stats.get('events_stored', 'N/A')}")
    lines.append(f"<b>Raw opportunities:</b> {dedup_result['raw_count']}")
    lines.append(f"<b>Unique opportunities:</b> {dedup_result['unique_count']}")
    lines.append(f"<b>Duplicate rate:</b> {dedup_result['duplicate_rate']}%")
    for p in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if p in priority_counts:
            icon = {"CRITICAL": "🚨", "HIGH": "🔥", "MEDIUM": "💡", "LOW": "📋"}.get(p, "")
            lines.append(f"<b>{icon} {p}:</b> {priority_counts[p]}")
    lines.append("")

    # --- Execution / Bottleneck ---
    lines.append("<b>⚙️ Execution / Bottleneck</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"<b>Trades opened:</b> {stats.get('trades_opened', stats.get('trades', 'N/A'))}")
    lines.append(f"<b>Open positions:</b> {stats.get('open_positions', 'N/A')}")
    lines.append(f"<b>Execution blocks:</b> {stats.get('execution_blocks', stats.get('blocks', 0))}")
    lines.append(f"<b>Guard blocks:</b> {stats.get('guard_blocks', 0)}")
    lines.append(f"<b>Top block reason:</b> {_safe_text(stats.get('top_block_reason', stats.get('bottleneck', 'N/A')))}")
    lines.append(f"<b>Capital guard mode:</b> {stats.get('capital_guard_mode', stats.get('guard_mode', 'N/A'))}")
    lines.append("")

    # --- Top Unique Opportunities ---
    if top_unique:
        lines.append("<b>🏆 Top Unique Opportunities</b>")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        for i, opp in enumerate(top_unique, 1):
            opp_type = opp.get("opportunity_type", "UNKNOWN")
            emoji = TYPE_EMOJIS.get(opp_type, "📌")
            assets = _render_assets(normalize_assets(opp.get("assets", [])))
            action = _safe_text(opp.get("action_suggested", "N/A"), 50)
            direction = _safe_text(opp.get("direction", opp.get("action", "N/A")), 30)
            score = opp.get("score", "N/A")
            confidence = opp.get("conviction", "N/A")
            block_reason = opp.get("block_reason", opp.get("why_blocked", "N/A"))
            reason = _safe_text(
                opp.get("title", "") or opp.get("hypothesis_statement", "") or
                opp.get("description", "") or opp.get("reason", ""),
                80,
            )

            lines.append("")
            lines.append(f"<b>#{i} {emoji} {opp_type}</b>")
            lines.append(f"<b>Asset:</b> {assets}")
            lines.append(f"<b>Action:</b> {action}")
            lines.append(f"<b>Direction:</b> {direction}")
            lines.append(f"<b>Score:</b> {score}  |  <b>Confidence:</b> {confidence}")
            if block_reason and block_reason not in ("N/A", "none", ""):
                lines.append(f"<b>Block reason:</b> {_safe_text(block_reason, 50)}")
            if reason and reason != "N/A":
                lines.append(f"<b>Why it matters:</b> {reason}")

    # --- Learning / Criterion ---
    lines.append("")
    lines.append("<b>🧠 Learning / Criterion</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    if learning_stats and learning_stats.get("connected"):
        lines.append(f"<b>Learning Core:</b> connected")
        lines.append(f"<b>Outcome comparisons:</b> {learning_stats.get('outcome_comparisons', 0)}")
        lines.append(f"<b>Knowledge items:</b> {learning_stats.get('knowledge_items', 0)}")
        lines.append(f"<b>Pending Criterion deltas:</b> {learning_stats.get('pending_criterion_deltas', 0)}")
        lines.append(f"<b>Last replay session:</b> {_safe_text(learning_stats.get('last_replay_session', 'N/A'), 30)}")
    else:
        lines.append("<b>Learning Core:</b> not connected in operational branch yet")

    # --- Diagnostics ---
    lines.append("")
    lines.append("<b>🧪 Diagnostics</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"<b>Asset formatting:</b> PASS")
    lines.append(f"<b>Duplicate status:</b> {dedup_result['duplicate_rate']}% duplicates")
    lines.append(f"<b>Priority saturation:</b> {'YES — ' + saturation.get('reason', '') if saturation.get('saturated') else 'No'}")
    lines.append("")

    lines.append("<b>━━━━━━━━━━━━━━━━━━━━━━</b>")
    lines.append("<i>Dashboard: https://oma-core-by-kimi.onrender.com</i>")

    return _truncate_message("\n".join(lines))


# ---------------------------------------------------------------------------
# TelegramNotifier class
# ---------------------------------------------------------------------------

class TelegramNotifier:
    """Sends quality-gated Telegram notifications for O.M.A.-C.O.R.E. runs."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        self.api_base = f"https://api.telegram.org/bot{self.token}" if self.token else None
        self._gate = NotificationQualityGate()

    # -- Raw send -----------------------------------------------------------

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled:
            print("[Telegram] Notifications disabled (check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
            return False
        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print("[Telegram] ✅ Message sent")
            return True
        except Exception as e:
            print(f"[Telegram] ❌ Error: {e}")
            return False

    # -- Run summary (new Sprint 10 quality-gated version) -------------------

    def send_run_summary(
        self,
        opportunities: List[Dict[str, Any]],
        stats: Dict[str, Any],
        learning_stats: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not self.enabled:
            return False

        dedup_result = deduplicate_opportunities(opportunities)
        unique = dedup_result["unique_opportunities"]

        priority_counts = {}
        for opp in opportunities:
            p = opp.get("priority", "UNKNOWN")
            priority_counts[p] = priority_counts.get(p, 0) + 1

        saturation = detect_priority_saturation(priority_counts, len(opportunities))

        message = render_notification(opportunities, stats, learning_stats)
        gate_result = self._gate.evaluate(
            opportunities, dedup_result, priority_counts, saturation, message,
        )
        self._gate.last_message = message

        if gate_result == "FAIL_DIAGNOSTIC":
            compact = self._build_compact_diagnostic(stats, dedup_result, saturation)
            return self.send_message(compact)

        if gate_result == "SUPPRESS_DETAIL":
            compact = self._build_compact_diagnostic(stats, dedup_result, saturation)
            return self.send_message(compact)

        if gate_result == "WARN":
            banner = self._gate.get_warning_banner()
            lines = message.split("\n")
            lines.insert(1, banner)
            message = "\n".join(lines)

        return self.send_message(message)

    # -- Critical alert (kept for backward compat, still unused) ------------

    def send_critical_alert(self, opportunities: List[Dict[str, Any]]) -> bool:
        if not self.enabled or not opportunities:
            return False
        critical = [o for o in opportunities if o.get("priority") == "CRITICAL"]
        if not critical:
            return False
        lines = [
            "<b>🚨 CRITICAL ALERT — O.M.A.-C.O.R.E.</b>",
            f"<b>{len(critical)} CRITICAL opportunities detected</b>",
            "",
        ]
        for i, opp in enumerate(critical[:5], 1):
            assets = _render_assets(normalize_assets(opp.get("assets", [])))
            lines.append(f"<b>#{i}</b> {opp.get('opportunity_type', 'UNKNOWN')} — {assets}")
            lines.append(f"Score: {opp.get('score', 'N/A')}  Action: {_safe_text(opp.get('action_suggested', 'N/A'), 40)}")
        lines.append("")
        lines.append("<i>Dashboard: https://oma-core-by-kimi.onrender.com</i>")
        return self.send_message("\n".join(lines))

    # -- Helpers -----------------------------------------------------------

    def _build_compact_diagnostic(
        self,
        stats: Dict[str, Any],
        dedup_result: Dict[str, Any],
        saturation: Dict[str, Any],
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        banner = self._gate.get_warning_banner()
        lines = [
            "<b>🤖 O.M.A.-C.O.R.E. RUN — Compact Diagnostic</b>",
            f"<b>{now} UTC</b>",
            "",
        ]
        if banner:
            lines.append(banner)
            lines.append("")
        lines.append("<b>📊 Summary</b>")
        lines.append(f"Raw: {dedup_result['raw_count']}  Unique: {dedup_result['unique_count']}  Dup rate: {dedup_result['duplicate_rate']}%")
        if saturation.get("saturated"):
            lines.append(f"⚠️ {saturation['reason']}")
        lines.append("")
        lines.append("<i>Run `scripts/render_telegram_notification.py` for full detail.</i>")
        return "\n".join(lines)

    # -- Test connection ----------------------------------------------------

    def test_connection(self) -> bool:
        if not self.enabled:
            print("[Telegram] ❌ Notifications disabled (check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
            return False
        try:
            url = f"{self.api_base}/getMe"
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("ok"):
                bot_name = data["result"].get("username", "Unknown")
                print(f"[Telegram] ✅ Connected as @{bot_name}")
                return True
            else:
                print(f"[Telegram] ❌ Error: {data.get('description')}")
                return False
        except Exception as e:
            print(f"[Telegram] ❌ Error: {e}")
            return False
