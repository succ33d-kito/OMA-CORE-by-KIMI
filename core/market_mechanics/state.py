"""Deterministic OHLCV features with explicit availability and provenance."""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from math import isfinite
from statistics import mean, stdev


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("market timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class MarketState:
    state_id: str
    symbol: str
    source_id: str
    observed_at: str
    as_of: str
    last_bar_closed_at: str
    timeframe_seconds: int
    lookback: int
    bar_count: int
    input_digest: str
    input_bars: tuple[tuple, ...]
    last_close: float
    last_return: float
    prior_high: float
    prior_low: float
    range_status: str
    volume_ratio: float | None
    return_volatility: float
    unknown_dimensions: tuple[str, ...]
    algorithm_version: str = "ohlcv-v1"

    def to_dict(self) -> dict:
        return asdict(self)


def build_market_state(symbol: str, bars: list[dict], *, source_id: str,
                       observed_at: datetime, as_of: datetime,
                       timeframe_seconds: int = 3600, lookback: int = 20) -> MarketState:
    """Use lookback previous bars plus the latest closed bar.

    `observed_at` is when this input batch became available to the consumer.
    Reject future/unclosed input rather than silently changing the sample.
    Volatility is per-bar sample standard deviation, not annualized.
    """
    observed_at, as_of = _aware(observed_at), _aware(as_of)
    if not symbol or not source_id or timeframe_seconds <= 0 or lookback < 2:
        raise ValueError("symbol, source, positive timeframe and lookback >= 2 required")
    if observed_at > as_of:
        raise ValueError("batch was not available at decision time")
    if len(bars) < lookback + 1:
        raise ValueError("insufficient closed bars")
    interval = timedelta(seconds=timeframe_seconds)
    validated = []
    previous = None
    for bar in bars:
        start = _aware(bar["time"])
        if previous is not None and start - previous != interval:
            raise ValueError("bars must be ordered, unique and contiguous")
        if start + interval > observed_at:
            raise ValueError("bar was still open when observed")
        values = {key: float(bar[key]) for key in ("open", "high", "low", "close", "volume")}
        if not all(isfinite(value) for value in values.values()):
            raise ValueError("non-finite OHLCV value")
        o, h, l, c, v = (values[key] for key in ("open", "high", "low", "close", "volume"))
        if min(o, h, l, c) <= 0 or v < 0 or not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError("invalid OHLCV bounds")
        validated.append({"time": start.isoformat(), **values})
        previous = start
    last_closed = previous + interval
    if as_of - last_closed > 2 * interval:
        raise ValueError("stale market data")
    window = validated[-(lookback + 1):]
    prior, latest = window[:-1], window[-1]
    high, low = max(b["high"] for b in prior), min(b["low"] for b in prior)
    status = "above_prior_range" if latest["close"] > high else (
        "below_prior_range" if latest["close"] < low else "inside_prior_range")
    returns = [window[i]["close"] / window[i - 1]["close"] - 1 for i in range(1, len(window))]
    baseline_volume = mean(b["volume"] for b in prior)
    digest = sha256(json.dumps(validated, sort_keys=True, allow_nan=False).encode()).hexdigest()
    identity = {"symbol": symbol, "source": source_id, "observed_at": observed_at.isoformat(),
                "as_of": as_of.isoformat(), "digest": digest, "timeframe": timeframe_seconds,
                "lookback": lookback, "algorithm": "ohlcv-v1"}
    state_id = sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return MarketState(
        state_id=state_id, symbol=symbol, source_id=source_id,
        observed_at=observed_at.isoformat(), as_of=as_of.isoformat(),
        last_bar_closed_at=last_closed.isoformat(), timeframe_seconds=timeframe_seconds,
        lookback=lookback,
        bar_count=len(validated), input_digest=digest,
        input_bars=tuple(tuple(b[key] for key in ("time", "open", "high", "low", "close", "volume")) for b in validated),
        last_close=latest["close"], last_return=returns[-1], prior_high=high, prior_low=low,
        range_status=status, volume_ratio=latest["volume"] / baseline_volume if baseline_volume else None,
        return_volatility=stdev(returns),
        unknown_dimensions=("order_flow", "resting_liquidity", "positioning", "derivatives", "capital_flow", "execution_depth"),
    )
