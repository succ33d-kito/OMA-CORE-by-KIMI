"""Position lifecycle states for Engine-owned internal positions."""

from enum import Enum


class PositionStatus(Enum):
    """Allowed internal position states for Sprint 15A structure."""

    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
