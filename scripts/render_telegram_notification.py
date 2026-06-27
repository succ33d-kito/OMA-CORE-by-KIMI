#!/usr/bin/env python3
"""
O.M.A.-C.O.R.E. Telegram Notification Dry-Run Renderer (Sprint 10)

Renders a sample notification to terminal without calling Telegram API.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.engines.telegram_notifier import (
    normalize_assets,
    deduplicate_opportunities,
    detect_priority_saturation,
    render_notification,
    get_learning_core_stats,
)


def sample_opportunities():
    return [
        {
            "id": "opp-001",
            "opportunity_type": "LONG_SETUP",
            "priority": "CRITICAL",
            "score": 95.0,
            "conviction": 0.85,
            "assets": ["BTC", "ETH"],
            "action_suggested": "buy",
            "direction": "long",
            "title": "BTC broke above resistance with strong volume",
            "block_reason": "N/A",
        },
        {
            "id": "opp-002",
            "opportunity_type": "SHORT_SETUP",
            "priority": "CRITICAL",
            "score": 92.0,
            "conviction": 0.80,
            "assets": '"SOL"',
            "action_suggested": "sell",
            "direction": "short",
            "title": "SOL overbought on daily",
            "block_reason": "capital_guard_emergency",
        },
        {
            "id": "opp-003",
            "opportunity_type": "MOMENTUM_PLAY",
            "priority": "HIGH",
            "score": 78.0,
            "conviction": 0.72,
            "assets": '["ADA", "OIL"]',
            "action_suggested": "buy",
            "direction": "long",
            "title": "ADA momentum play",
        },
        {
            "id": "opp-004",
            "opportunity_type": "LONG_SETUP",
            "priority": "CRITICAL",
            "score": 95.0,
            "conviction": 0.85,
            "assets": ["BTC", "ETH"],
            "action_suggested": "buy",
            "direction": "long",
            "title": "BTC broke above resistance with strong volume",
        },
        {
            "id": "opp-005",
            "opportunity_type": "MACRO_TAILWIND",
            "priority": "MEDIUM",
            "score": 60.0,
            "conviction": 0.55,
            "assets": "BTC, ETH, SOL",
            "action_suggested": "watch",
            "direction": "neutral",
        },
        {
            "id": "opp-006",
            "opportunity_type": "TECHNICAL_WATCH",
            "priority": "LOW",
            "score": 42.0,
            "conviction": 0.40,
            "assets": None,
            "action_suggested": "monitor",
            "direction": "neutral",
        },
    ]


def main():
    print("=" * 60)
    print("  O.M.A.-C.O.R.E. Telegram Notification — Dry Run")
    print("=" * 60)
    print()
    print("No message will be sent to Telegram.")
    print()

    opps = sample_opportunities()

    # Demonstrate normalize_assets
    print(">>> normalize_assets examples")
    for val in [
        "BTC",
        ["BTC", "ETH"],
        '["BTC", "ETH"]',
        '"BTC"',
        "BTC, ETH",
        None,
        "",
        [],
        '"SOL"',
    ]:
        result = normalize_assets(val)
        print(f"  normalize_assets({val!r}) -> {result}")
    print()

    # Demonstrate deduplicate
    print(">>> deduplicate_opportunities")
    dedup = deduplicate_opportunities(opps)
    print(f"  Raw: {dedup['raw_count']}")
    print(f"  Unique: {dedup['unique_count']}")
    print(f"  Duplicate rate: {dedup['duplicate_rate']}%")
    print()

    # Demonstrate priority saturation
    print(">>> detect_priority_saturation")
    from collections import Counter
    counts = Counter(o.get("priority", "UNKNOWN") for o in opps)
    sat = detect_priority_saturation(dict(counts), len(opps))
    print(f"  Saturated: {sat['saturated']}")
    print(f"  Reason: {sat.get('reason', 'N/A')}")
    print()

    # Render full notification
    print(">>> Full notification text")
    print("---BEGIN---")
    stats = {
        "events_processed": 42,
        "events_stored": 15,
        "opportunities_generated": 100,
        "trades_opened": 3,
        "open_positions": 2,
        "execution_blocks": 15,
        "guard_blocks": 3,
        "top_block_reason": "Execution Capacity Limit",
        "capital_guard_mode": "active",
    }
    learning_stats = get_learning_core_stats()
    message = render_notification(opps, stats, learning_stats)
    print(message)
    print("---END---")
    print()

    print("=" * 60)
    print("  Dry run complete — no messages sent.")
    print("=" * 60)


if __name__ == "__main__":
    main()
