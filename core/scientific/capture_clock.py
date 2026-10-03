"""Fail-closed live clock evidence; never correct or synthesize a timestamp."""
from math import isfinite


class ClockHealthError(ValueError):
    pass


def preflight(started, received, server, elapsed):
    """Bound uncertainty using the provider's HTTPS time and monotonic RTT.

    v1 requires RTT <= 2s and host/provider skew <= 1s. These are
    operational admission limits, not permission to tolerate server-ahead.
    """
    wall = (received - started).total_seconds()
    if not isfinite(elapsed) or elapsed < 0 or elapsed > 2 or abs(wall - elapsed) > .1:
        raise ClockHealthError('clock health: uncertain RTT or wall-clock discontinuity')
    if server > received:
        raise ClockHealthError('server clock ahead of local receipt clock')
    if (received - server).total_seconds() > 1:
        raise ClockHealthError('clock health: host clock ahead of reference')
    return dict(contract='pit-clock-health-v1', reference='Binance HTTPS serverTime',
                checked_at=received.isoformat(), request_started_at=started.isoformat(),
                round_trip_seconds=elapsed, max_round_trip_seconds=2,
                offset_lower_seconds=(started-server).total_seconds(),
                offset_upper_seconds=(received-server).total_seconds(),
                max_host_ahead_seconds=1, wall_monotonic_tolerance_seconds=.1)


def continuous(started, received, elapsed):
    if not isfinite(elapsed) or elapsed < 0 or abs((received-started).total_seconds()-elapsed) > .1:
        raise ClockHealthError('clock health: wall-clock discontinuity during capture')
