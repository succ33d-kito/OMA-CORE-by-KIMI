"""outcome_evaluator.py — Shared logic for evaluating hypotheses against outcomes."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.schemas.outcome_comparison_schema import OutcomeComparison, ComparisonType, Verdict, ErrorType
from core.schemas.hypothesis_schema import HypothesisStatus
from core.scientific.scientific_store import ScientificStore
from core.scientific.outcome_bridge import TYPE_DIRECTION_MAP


def parse_hypothesis_id(raw: str, store: ScientificStore) -> Optional[str]:
    """Resolve a hypothesis ID or prefix from the store."""
    if not raw or raw == "all":
        return raw
    hypotheses = store.list_hypotheses(limit=10000)
    for h in hypotheses:
        if h.id == raw:
            return raw
    matches = [h.id for h in hypotheses if h.id.startswith(raw)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"  Multiple hypotheses match prefix '{raw}': {matches[:5]}...")
        return None
    return raw


def auto_detect_verdict(actual_outcome: str,
                        hypothesis_direction: str) -> Tuple[Verdict, float]:
    """Auto-detect verdict from outcome text and expected direction."""
    outcome_lower = actual_outcome.lower()

    direction_up = {"up", "rise", "rose", "gain", "gained", "increased",
                    "higher", "bullish", "surged", "rally", "positive",
                    "green", "breakout", "upward"}
    direction_down = {"down", "drop", "dropped", "fell", "fall", "decline",
                      "decreased", "lower", "bearish", "crashed", "plunge",
                      "negative", "red", "breakdown", "downward"}
    confirmed_words = {"confirmed", "correct", "valid", "accurate", "true",
                       "matched", "hit", "achieved"}
    rejected_words = {"rejected", "wrong", "incorrect", "false", "opposite",
                      "failed", "missed", "invalid"}
    inconclusive_words = {"inconclusive", "uncertain", "unclear", "pending",
                          "mixed", "neutral", "flat", "unchanged",
                          "no movement", "sideways"}

    up_count = sum(1 for w in direction_up if w in outcome_lower)
    down_count = sum(1 for w in direction_down if w in outcome_lower)

    for w in confirmed_words:
        if w in outcome_lower:
            return Verdict.CONFIRMED, 0.85
    for w in rejected_words:
        if w in outcome_lower:
            return Verdict.REJECTED, 0.80
    for w in inconclusive_words:
        if w in outcome_lower:
            return Verdict.INCONCLUSIVE, 0.70

    if hypothesis_direction == "bullish" and up_count > down_count:
        return Verdict.CONFIRMED, 0.75
    if hypothesis_direction == "bullish" and down_count > up_count:
        return Verdict.REJECTED, 0.70
    if hypothesis_direction == "bearish" and down_count > up_count:
        return Verdict.CONFIRMED, 0.75
    if hypothesis_direction == "bearish" and up_count > down_count:
        return Verdict.REJECTED, 0.70
    if hypothesis_direction == "neutral" and up_count == down_count:
        return Verdict.CONFIRMED, 0.60

    if up_count > 0 and down_count > 0:
        return Verdict.INCONCLUSIVE, 0.50

    return Verdict.INCONCLUSIVE, 0.40


def compute_outcome_score(verdict: Verdict, confidence: float,
                          actual_outcome: str,
                          hypothesis: Any) -> Dict[str, Any]:
    score_map = {
        Verdict.CONFIRMED: 100,
        Verdict.PARTIALLY_CONFIRMED: 60,
        Verdict.INCONCLUSIVE: 30,
        Verdict.REJECTED: 0,
    }
    base_score = score_map.get(verdict, 0)
    return {
        "outcome_score": base_score,
        "prediction_confidence": hypothesis.confidence if hasattr(hypothesis, 'confidence') else 0.5,
        "actual_outcome_text": actual_outcome[:200],
    }


def evaluate_hypotheses(
    hypothesis_ids: List[str],
    actual_outcomes: Dict[str, str],
    store: ScientificStore,
    dry_run: bool = True,
) -> Dict[str, Any]:
    results = []
    hypotheses = store.list_hypotheses(limit=10000)

    for hyp in hypotheses:
        if hypothesis_ids and hyp.id not in hypothesis_ids and "all" not in hypothesis_ids:
            continue

        actual = actual_outcomes.get(hyp.id) or actual_outcomes.get("all")
        if not actual:
            continue

        direction = "neutral"
        for opp_type, d in TYPE_DIRECTION_MAP.items():
            if opp_type in hyp.title or opp_type in hyp.description:
                direction = d
                break

        verdict, auto_confidence = auto_detect_verdict(actual, direction)
        metrics = compute_outcome_score(verdict, auto_confidence, actual, hyp)
        error_type = None
        error_detail = None

        if verdict == Verdict.REJECTED:
            if "time" in actual.lower() or "delay" in actual.lower():
                error_type = ErrorType.WRONG_TIMING
                error_detail = "Prediction timing was incorrect"
            elif "hypothesis" in actual.lower() or "direction" in actual.lower():
                error_type = ErrorType.WRONG_HYPOTHESIS
                error_detail = "Predicted direction was incorrect"
            elif "shock" in actual.lower() or "unexpected" in actual.lower():
                error_type = ErrorType.EXTERNAL_SHOCK
                error_detail = "External event invalidated the prediction"
            else:
                error_type = ErrorType.WRONG_HYPOTHESIS
                error_detail = "Prediction did not match actual outcome"

        comparison = OutcomeComparison(
            id=f"cmp_{hyp.id[:24]}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            hypothesis_id=hyp.id,
            verdict=verdict,
            comparison_type=ComparisonType.EXECUTED,
            predicted_consequence=hyp.predicted_consequence,
            actual_outcome=actual[:500],
            comparison_confidence=auto_confidence,
            compared_at=datetime.now(timezone.utc),
            error_type=error_type,
            error_detail=error_detail,
        )

        if not dry_run:
            store.create_outcome_comparison(comparison)

        results.append({
            "hypothesis_id": hyp.id,
            "hypothesis_title": hyp.title[:80],
            "verdict": verdict.value,
            "comparison_id": comparison.id,
            "outcome_score": metrics["outcome_score"],
            "comparison_confidence": auto_confidence,
            "error_type": error_type.value if error_type else None,
            "actual_outcome": actual[:100],
        })

    return {
        "total_hypotheses": len(hypotheses),
        "evaluated": len(results),
        "dry_run": dry_run,
        "results": results,
    }


def print_evaluation_report(result: Dict[str, Any]) -> None:
    print()
    print("=" * 60)
    print("  Outcome Evaluation Report")
    print("=" * 60)
    print(f"  Hypotheses available: {result.get('total_hypotheses')}")
    print(f"  Hypotheses evaluated: {result.get('evaluated')}")
    print(f"  Mode: {'DRY RUN' if result.get('dry_run') else 'COMMIT'}")
    print()

    if not result.get("results"):
        print("  No hypotheses evaluated.")
        return

    verdicts: Dict[str, int] = {}
    for r in result["results"]:
        v = r["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1

    print("--- Verdict Distribution ---")
    for v, c in sorted(verdicts.items(), key=lambda x: -x[1]):
        print(f"  {v:25s} {c}")
    print()

    print("--- Results ---")
    for r in result["results"]:
        print(f"  [{r['verdict']:20s}] score={r['outcome_score']:3d}  "
              f"{r['hypothesis_title'][:60]}")
        if r.get("error_type"):
            print(f"  {'':25s} error={r['error_type']}")
    print()

    if result.get("dry_run"):
        print("  DRY RUN — no data was modified.")
        print("  Pass --commit to write to scientific.db.")
