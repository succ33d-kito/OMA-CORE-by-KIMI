"""
outcome_bridge.py — Opportunity → Hypothesis Bridge (Stage 10, part 1).

Converts operational opportunities from oma_core.db into scientific hypotheses
in scientific.db. Each opportunity generates one hypothesis in FORMULATED status.

Never modifies operational data. Never modifies execution.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.scientific.scientific_store import ScientificStore


# Mapping from opportunity type → expected direction/prediction
TYPE_DIRECTION_MAP = {
    "LONG_SETUP": "bullish",
    "SHORT_SETUP": "bearish",
    "MOMENTUM_PLAY": "momentum",
    "AVOID_OR_SHORT": "bearish",
    "SAFE_HAVEN_FLOW": "risk_off",
    "RISK_OFF": "bearish",
    "WHALE_ACCUMULATION": "bullish",
    "WHALE_DISTRIBUTION": "bearish",
    "VIRAL_MOMENTUM": "volatile",
    "POST_EARNINGS_RUN": "bullish",
    "POST_EARNINGS_DROP": "bearish",
    "MACRO_TAILWIND": "bullish",
    "MACRO_HEADWIND": "bearish",
    "REGULATORY_TAILWIND": "bullish",
    "REGULATORY_HEADWIND": "bearish",
    "SENTIMENT_TURN_BULL": "bullish",
    "SENTIMENT_TURN_BEAR": "bearish",
    "TECHNICAL_BREAKOUT": "bullish",
    "TECHNICAL_BREAKDOWN": "bearish",
    "ARB_OPPORTUNITY": "convergence",
    "WATCHLIST_ADD": "neutral",
    "NEWS_DRIVEN": "volatile",
    "MONITOR_MACRO": "neutral",
    "MONITOR_COMPLIANCE": "neutral",
    "MONITOR_GEO": "neutral",
    "EARNINGS_NEUTRAL": "neutral",
    "SENTIMENT_WATCH": "neutral",
    "TECHNICAL_WATCH": "neutral",
    "WHALE_WATCH": "neutral",
}


OPPORTUNITY_QUERY = """
    SELECT id, event_id, title, description, opportunity_type, asset_class,
           assets, score, conviction, priority, action_suggested, risk_level,
           timestamp, expires_at, status
    FROM opportunities
    ORDER BY timestamp DESC
"""


class OutcomeBridge:
    """Bridge that converts operational opportunities into scientific hypotheses."""

    def __init__(self, operational_db: str = "oma_core.db",
                 scientific_db: str = "scientific.db"):
        self.operational_db = operational_db
        self.scientific_store = ScientificStore(scientific_db)

    def fetch_opportunities(self, limit: Optional[int] = None,
                            min_score: float = 0.0) -> List[Dict[str, Any]]:
        """Read opportunities from the operational database. Read-only."""
        if not os.path.exists(self.operational_db):
            return []
        conn = sqlite3.connect(self.operational_db)
        conn.row_factory = sqlite3.Row
        query = OPPORTUNITY_QUERY
        params: List = []
        if limit:
            query = query.rstrip(";") + f" LIMIT {limit}"
        rows = conn.execute(query).fetchall()
        conn.close()
        return [
            dict(r) for r in rows
            if r.get("score", 0) >= min_score
        ]

    def opportunity_to_hypothesis(self, opp: Dict[str, Any]) -> Hypothesis:
        """Convert a single opportunity dict into a Hypothesis object."""
        opp_type = opp.get("opportunity_type", "UNKNOWN")
        direction = TYPE_DIRECTION_MAP.get(opp_type, "neutral")
        assets_raw = opp.get("assets", "[]")
        if isinstance(assets_raw, str):
            try:
                assets = json.loads(assets_raw)
            except (json.JSONDecodeError, TypeError):
                assets = [assets_raw]
        else:
            assets = assets_raw or []
        assets_str = ", ".join(str(a) for a in assets) if assets else "N/A"

        score = opp.get("score", 50.0)
        conviction = opp.get("conviction", 50.0)

        # Build predicted consequence from action and direction
        action = opp.get("action_suggested", "Monitor")

        predicted_consequence = (
            f"Opportunity type {opp_type} ({direction}) suggests: {action}. "
            f"If valid, the expected outcome is {direction} movement "
            f"for assets [{assets_str}] over the evaluation window."
        )

        conditions = (
            f"Opportunity ID: {opp.get('id', 'unknown')}. "
            f"Type: {opp_type}. Assets: {assets_str}. "
            f"Score: {score}/100. Conviction: {conviction}/100. "
            f"Priority: {opp.get('priority', 'unknown')}. "
            f"Risk: {opp.get('risk_level', 'unknown')}. "
            f"Asset class: {opp.get('asset_class', 'unknown')}. "
            f"Created: {opp.get('timestamp', 'unknown')}."
        )

        invalidation = (
            f"The {direction} movement does not materialize within the expected "
            f"time horizon, or the opposite movement occurs. "
            f"The opportunity's core reasoning is contradicted by market data."
        )

        title = opp.get("title", "Untitled opportunity")
        title = f"[BRIDGE] {opp_type}: {title[:80]}"

        # Initial confidence: normalized from conviction (0-100 → 0-1)
        confidence = max(0.1, min(conviction / 100.0, 0.95))

        return Hypothesis(
            id=f"hyp_{opp.get('event_id', opp.get('id', 'unknown'))}",
            title=title[:200],
            description=(
                f"Bridged from opportunity {opp.get('id', 'unknown')}. "
                f"Direction: {direction}. "
                f"Reasoning: {conditions}"
            )[:500],
            predicted_consequence=predicted_consequence[:500],
            conditions=conditions[:500],
            invalidation_conditions=invalidation[:300],
            confidence=confidence,
            status=HypothesisStatus.FORMULATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def bridge_all(self, limit: Optional[int] = None,
                   min_score: float = 0.0,
                   dry_run: bool = True) -> Dict[str, Any]:
        """Bridge all eligible opportunities into hypotheses.

        Args:
            limit: Max opportunities to process.
            min_score: Minimum opportunity score threshold.
            dry_run: If True, preview only. If False, persist to scientific.db.

        Returns:
            Summary dict with counts and details.
        """
        opps = self.fetch_opportunities(limit=limit, min_score=min_score)
        if not opps:
            return {
                "opportunities_found": 0,
                "hypotheses_generated": 0,
                "dry_run": dry_run,
                "existing_hypotheses_skipped": 0,
                "hypotheses": [],
            }

        # Get existing hypothesis IDs to avoid duplicates
        existing = self.scientific_store.list_hypotheses(limit=10000)
        existing_ids = set(h.id for h in existing)

        generated = []
        skipped = 0
        for opp in opps:
            hypothesis = self.opportunity_to_hypothesis(opp)
            if hypothesis.id in existing_ids:
                skipped += 1
                continue
            if not dry_run:
                self.scientific_store.create_hypothesis(
                    title=hypothesis.title,
                    description=hypothesis.description,
                    predicted_consequence=hypothesis.predicted_consequence,
                    conditions=hypothesis.conditions,
                    invalidation_conditions=hypothesis.invalidation_conditions,
                    confidence=hypothesis.confidence,
                    hypothesis_id=hypothesis.id,
                )
            generated.append(hypothesis)

        return {
            "opportunities_found": len(opps),
            "hypotheses_generated": len(generated),
            "hypotheses_skipped_duplicates": skipped,
            "dry_run": dry_run,
            "hypotheses": generated,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        opps = self.fetch_opportunities()
        existing = self.scientific_store.list_hypotheses(limit=10000)
        bridged_ids = set(h.id for h in existing)
        bridgeable = sum(
            1 for o in opps
            if f"hyp_{o.get('event_id', o.get('id', ''))}" not in bridged_ids
        )
        return {
            "total_opportunities": len(opps),
            "total_hypotheses_in_scientific": len(existing),
            "bridgeable_opportunities": bridgeable,
            "already_bridged": len(opps) - bridgeable,
        }
