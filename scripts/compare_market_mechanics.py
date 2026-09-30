"""Offline preregistered entry comparison. See research/MM_H1_PROTOCOL.md."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from math import sin
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.scientific.mechanics_comparison import compare


def synthetic_bars(count=720):
    """Deterministic software fixture. Never evidence of market performance."""
    rows, price = [], 100.0
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    for i in range(count):
        close = price * (1 + .001 * sin(i / 7) + .0005 + (.015 if i % 31 == 0 else 0))
        rows.append(dict(time=start + timedelta(hours=i), open=price,
                         high=max(price, close)*1.002, low=min(price, close)*.998,
                         close=close, volume=300 if i % 31 == 0 else 100))
        price = close
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="JSON array of hourly OHLCV with aware ISO time")
    source.add_argument("--synthetic-smoke", action="store_true")
    parser.add_argument("--symbol", default="BTC")
    parser.add_argument("--source", default=None, help="Required provenance for historical input")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.synthetic_smoke:
        bars, kind, provenance = synthetic_bars(), "synthetic", "synthetic:software-test:v1"
    else:
        if not args.source:
            parser.error("--source is required for historical input")
        bars = json.loads(args.input.read_text())
        for bar in bars:
            bar["time"] = datetime.fromisoformat(bar["time"].replace("Z", "+00:00"))
        kind, provenance = "historical", args.source
    report = compare(bars, symbol=args.symbol, source_id=provenance, data_kind=kind)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps({"verdict": report["verdict"], "bars": report["bars"],
                      "scope": report["scope"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
