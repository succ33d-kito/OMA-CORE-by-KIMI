"""Order lifecycle states for Engine-owned internal orders."""

from enum import Enum


class OrderStatus(Enum):
    """Allowed internal order states for Sprint 15A structure."""

    NEW = "NEW"
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
