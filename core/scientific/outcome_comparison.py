"""O.M.A.-C.O.R.E. Outcome Comparison Logic

Transforms a hypothesis and an actual outcome into a structured
OutcomeComparison with a verdict, optional error classification,
and comparison confidence.

Manual CLI workflow — no automation, no pipeline integration.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from core.schemas.outcome_comparison_schema import (
    OutcomeComparison, Verdict, ErrorType, ComparisonType,
)
from core.schemas.hypothesis_schema import Hypothesis


DIRECTION_UP = {"up", "increase", "rise", "rally", "rallies", "rallied", "rallying", "gain", "gained", "higher", "bullish", "long", "buy", "surge", "surged", "surges", "jump", "jumped", "jumps", "climb", "climbed", "climbs", "soar", "soared", "soars", "boom", "boomed", "advance", "advanced", "advances"}
DIRECTION_DOWN = {"down", "decrease", "drop", "dropped", "drops", "fell", "fall", "falls", "fallen", "decline", "declined", "declines", "lower", "bearish", "short", "sell", "crash", "crashed", "crashes", "plunge", "plunged", "plunges", "dump", "dumped", "slide", "slid", "sink", "sank", "dip", "dipped", "dips", "retreat", "retreated", "retreats"}


def _extract_direction(text: str) -> Optional[str]:
    text_lower = text.lower()
    if any(w in text_lower for w in DIRECTION_UP):
        return "up"
    if any(w in text_lower for w in DIRECTION_DOWN):
        return "down"
    return None


def _extract_numeric(text: str) -> Optional[float]:
    """Extract a numeric value from text, with sign inferred from context."""
    matches = re.findall(r"[-+]?\d*\.?\d+%?", text)
    if not matches:
        return None
    raw = matches[0]
    if raw.endswith("%"):
        value = float(raw[:-1]) / 100.0
    else:
        value = float(raw)
    if value >= 0 and _extract_direction(text) == "down":
        return -value
    return value


def auto_detect_verdict(
    predicted: str, actual: str
) -> Optional[Verdict]:
    """Attempt to auto-detect verdict by heuristic matching.

    Checks numeric values first (higher precision), then direction
    words as fallback. Returns None when the comparison is ambiguous.
    """
    pred_num = _extract_numeric(predicted)
    actual_num = _extract_numeric(actual)

    if pred_num is not None and actual_num is not None:
        same_sign = (pred_num >= 0 and actual_num >= 0) or (pred_num < 0 and actual_num < 0)
        if same_sign:
            abs_diff = abs(actual_num - pred_num)
            magnitude_error = abs_diff / max(abs(pred_num), 0.001)
            if magnitude_error <= 0.3 or abs_diff <= 0.015:
                return Verdict.CONFIRMED
            return Verdict.INCONCLUSIVE
        else:
            return Verdict.REJECTED

    pred_dir = _extract_direction(predicted)
    actual_dir = _extract_direction(actual)

    if pred_dir and actual_dir:
        if pred_dir == actual_dir:
            return Verdict.CONFIRMED
        return Verdict.REJECTED

    return None


def compare_outcome(
    hypothesis: Hypothesis,
    actual_outcome: str,
    verdict: Optional[Verdict] = None,
    comparison_confidence: float = 0.8,
    comparison_type: ComparisonType = ComparisonType.EXECUTED,
    error_type: Optional[ErrorType] = None,
    error_detail: Optional[str] = None,
    tolerance_applied: Optional[Dict[str, Any]] = None,
) -> OutcomeComparison:
    """Compare a hypothesis's predicted consequence with an actual outcome.

    If verdict is not provided, attempts auto-detection via
    auto_detect_verdict(). Falls back to INCONCLUSIVE when
    auto-detection is uncertain.
    """
    if verdict is None:
        verdict = auto_detect_verdict(
            hypothesis.predicted_consequence, actual_outcome
        ) or Verdict.INCONCLUSIVE

    if verdict == Verdict.REJECTED and error_type is None:
        error_type = classify_error(hypothesis, actual_outcome, verdict)

    if tolerance_applied is None:
        tolerance_applied = {"magnitude": 0.3, "timing": 0.5}

    return OutcomeComparison(
        id=str(uuid.uuid4()),
        hypothesis_id=hypothesis.id,
        verdict=verdict,
        comparison_type=comparison_type,
        predicted_consequence=hypothesis.predicted_consequence,
        actual_outcome=actual_outcome,
        comparison_confidence=max(0.0, min(1.0, comparison_confidence)),
        compared_at=datetime.now(timezone.utc),
        error_type=error_type,
        error_detail=error_detail,
        tolerance_applied=tolerance_applied,
    )


def classify_error(
    hypothesis: Hypothesis,
    actual_outcome: str,
    verdict: Verdict,
) -> Optional[ErrorType]:
    """Classify the error type for a rejected or unexpected outcome.

    Uses simple heuristics. Human override is always available.
    """
    if verdict == Verdict.REJECTED:
        pred_dir = _extract_direction(hypothesis.predicted_consequence)
        actual_dir = _extract_direction(actual_outcome)

        if pred_dir and actual_dir and pred_dir == actual_dir:
            return ErrorType.WRONG_TIMING
        if "shock" in actual_outcome.lower() or "unexpected" in actual_outcome.lower():
            return ErrorType.EXTERNAL_SHOCK
        return ErrorType.WRONG_HYPOTHESIS

    if verdict in (Verdict.CONFIRMED, Verdict.INCONCLUSIVE):
        return None

    return None
