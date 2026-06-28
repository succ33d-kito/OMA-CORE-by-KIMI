"""
Yahoo Data Integrity Guard

Validates market quotes from Yahoo Finance before they become events or opportunities.
Prevents missing/invalid price data from being transformed into false CRITICAL opportunities.
"""

import math
from typing import Optional, Tuple, Dict, Any


# ---------------------------------------------------------------------------
# Quote validation
# ---------------------------------------------------------------------------

# Asset classes where missing volume is normal
VOLUME_OPTIONAL = {"forex", "index", "commodity"}

# Suspicious extreme return threshold (anything >= 80% is likely data error)
MAX_REASONABLE_CHANGE_PCT = 80.0


def validate_quote(close: Any, prev_close: Any, symbol: str,
                   asset_class: Optional[str] = None) -> Tuple[bool, str]:
    """Validate a market quote from Yahoo Finance.

    Returns (is_valid, reason).
    If is_valid is False, the quote should be skipped or downgraded.
    """
    ac = (asset_class or "").lower()

    # Close price checks
    if close is None:
        return False, "invalid_price_none"
    try:
        close_f = float(close)
    except (ValueError, TypeError):
        return False, "invalid_price_type"
    if math.isnan(close_f) or math.isinf(close_f):
        return False, "invalid_price_nan_or_inf"
    if close_f <= 0:
        return False, "invalid_price_zero_or_negative"

    # Previous close checks
    if prev_close is None:
        return False, "missing_previous_close"
    try:
        prev_f = float(prev_close)
    except (ValueError, TypeError):
        return False, "invalid_previous_close_type"
    if math.isnan(prev_f) or math.isinf(prev_f):
        return False, "invalid_previous_close_nan_or_inf"
    if prev_f <= 0:
        return False, "invalid_previous_close_zero_or_negative"

    # Change percent check — extreme returns without verification
    change_pct = ((close_f - prev_f) / prev_f) * 100
    if abs(change_pct) >= MAX_REASONABLE_CHANGE_PCT:
        return False, f"suspicious_extreme_return_{change_pct:+.0f}pct"

    return True, ""


def validate_quote_for_event(close: Any, prev_close: Any, symbol: str,
                              asset_class: Optional[str] = None) -> Dict[str, Any]:
    """Validate and return diagnostic info.

    Returns dict with:
      - valid: bool
      - reason: str
      - close/prev_close/change_pct as floats if valid
    """
    is_valid, reason = validate_quote(close, prev_close, symbol, asset_class)
    result: Dict[str, Any] = {
        "valid": is_valid,
        "reason": reason,
        "close": None,
        "prev_close": None,
        "change_pct": None,
    }
    if is_valid:
        cf = float(close)
        pf = float(prev_close)
        result["close"] = cf
        result["prev_close"] = pf
        result["change_pct"] = ((cf - pf) / pf) * 100
    else:
        try:
            result["close"] = float(close) if close is not None else None
        except (ValueError, TypeError):
            result["close"] = None
        try:
            result["prev_close"] = float(prev_close) if prev_close is not None else None
        except (ValueError, TypeError):
            result["prev_close"] = None
    return result


# ---------------------------------------------------------------------------
# Opportunity-level guardrail
# ---------------------------------------------------------------------------

def detect_data_quality_issue(event: Any) -> Tuple[bool, str]:
    """Check if an event should be treated as a data quality issue.

    Returns (is_issue, reason).
    If True, the opportunity should be capped/downgraded.
    """
    if event.source != "yahoo_finance":
        return False, ""

    # Check event metadata for price/change anomalies
    meta = getattr(event, "metadata", None) or {}
    if isinstance(meta, dict):
        price = meta.get("price")
        change = meta.get("change_percent")
        if price is not None and price <= 0:
            return True, "invalid_price_zero_or_negative"
        if change is not None and abs(change) >= MAX_REASONABLE_CHANGE_PCT:
            return True, f"suspicious_extreme_return_{change:+.0f}pct"

    # Check event title for -100% or $0.00 patterns
    title = getattr(event, "title", "") or ""
    summary = getattr(event, "summary", "") or ""
    text = title + " " + summary
    if "$0.00" in text or "$0.0 " in text or "$0 " in text:
        return True, "price_zero_in_text"
    if "-100.00%" in text:
        return True, "minus_100_pct_in_text"

    # Check assets for invalid price
    assets = getattr(event, "assets", None) or []
    for a in assets:
        pa = getattr(a, "price_at_event", None)
        if pa is not None and pa <= 0:
            return True, f"asset_price_zero: {getattr(a, 'symbol', 'unknown')}"

    return False, ""


def should_downgrade_opportunity(event: Any) -> Tuple[bool, Dict[str, Any]]:
    """Determine if an opportunity should be downgraded and by how much.

    Returns (should_downgrade, override_dict).
    override_dict can contain max_score, max_priority, max_conviction, etc.
    """
    is_issue, reason = detect_data_quality_issue(event)
    if not is_issue:
        return False, {}

    return True, {
        "max_score": 30.0,
        "max_priority": "MEDIUM",
        "max_conviction": 30.0,
        "action_suggested": "Review data quality",
        "risk_level": "DATA_QUALITY",
        "data_quality_reason": reason,
    }
