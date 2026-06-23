"""OSIRIS Profile Models — Trader, Entrepreneur, Creator"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class ProfileType(Enum):
    TRADER = "trader"
    ENTREPRENEUR = "entrepreneur"
    CREATOR = "creator"


@dataclass
class TraderPreferences:
    markets: List[str] = field(default_factory=lambda: ["crypto", "stocks", "forex"])
    risk_tolerance: str = "medium"
    max_position_size_pct: float = 5.0
    preferred_strategies: List[str] = field(default_factory=lambda: ["swing", "momentum"])
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 6.0
    min_conviction: float = 60.0
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "markets": self.markets,
            "risk_tolerance": self.risk_tolerance,
            "max_position_size_pct": self.max_position_size_pct,
            "preferred_strategies": self.preferred_strategies,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "min_conviction": self.min_conviction,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TraderPreferences":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EntrepreneurPreferences:
    industries: List[str] = field(default_factory=lambda: ["tech", "ai", "saas", "automation"])
    risk_tolerance: str = "medium"
    min_opportunity_score: float = 50.0
    preferred_business_types: List[str] = field(default_factory=lambda: ["startup", "side_hustle", "arbitrage"])
    max_investment_hours_week: int = 20
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "industries": self.industries,
            "risk_tolerance": self.risk_tolerance,
            "min_opportunity_score": self.min_opportunity_score,
            "preferred_business_types": self.preferred_business_types,
            "max_investment_hours_week": self.max_investment_hours_week,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EntrepreneurPreferences":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CreatorPreferences:
    platforms: List[str] = field(default_factory=lambda: ["youtube", "tiktok", "instagram", "x"])
    content_categories: List[str] = field(default_factory=lambda: ["finance", "tech", "news"])
    risk_tolerance: str = "low"
    min_viral_potential: float = 30.0
    posting_frequency: str = "daily"
    monetization_goal: str = "growth"
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "platforms": self.platforms,
            "content_categories": self.content_categories,
            "risk_tolerance": self.risk_tolerance,
            "min_viral_potential": self.min_viral_potential,
            "posting_frequency": self.posting_frequency,
            "monetization_goal": self.monetization_goal,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CreatorPreferences":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


ProfilePreferences = TraderPreferences | EntrepreneurPreferences | CreatorPreferences


@dataclass
class UserProfile:
    id: str
    name: str
    profile_type: ProfileType
    preferences: ProfilePreferences
    watchlist: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "profile_type": self.profile_type.value,
            "preferences": self.preferences.to_dict() if hasattr(self.preferences, 'to_dict') else self.preferences,
            "watchlist": self.watchlist,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        profile_type = ProfileType(data["profile_type"])
        pref_data = data.get("preferences", {})
        if profile_type == ProfileType.TRADER:
            preferences = TraderPreferences.from_dict(pref_data)
        elif profile_type == ProfileType.ENTREPRENEUR:
            preferences = EntrepreneurPreferences.from_dict(pref_data)
        else:
            preferences = CreatorPreferences.from_dict(pref_data)

        return cls(
            id=data["id"],
            name=data["name"],
            profile_type=profile_type,
            preferences=preferences,
            watchlist=data.get("watchlist", []),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else datetime.now(timezone.utc),
            metadata=data.get("metadata", {}),
        )


class ProfileRegistry:
    def __init__(self, db=None):
        self.db = db
        self._cache: Dict[str, UserProfile] = {}

    def register(self, profile: UserProfile) -> None:
        self._cache[profile.id] = profile
        if self.db:
            self._persist(profile)

    def get(self, profile_id: str) -> Optional[UserProfile]:
        if profile_id in self._cache:
            return self._cache[profile_id]
        if self.db:
            return self._load(profile_id)
        return None

    def get_by_type(self, profile_type: ProfileType) -> List[UserProfile]:
        return [p for p in self._cache.values() if p.profile_type == profile_type]

    def create_default(self, name: str, profile_type: ProfileType) -> UserProfile:
        import uuid
        if profile_type == ProfileType.TRADER:
            preferences = TraderPreferences()
        elif profile_type == ProfileType.ENTREPRENEUR:
            preferences = EntrepreneurPreferences()
        else:
            preferences = CreatorPreferences()

        profile = UserProfile(
            id=str(uuid.uuid4()),
            name=name,
            profile_type=profile_type,
            preferences=preferences,
        )
        self.register(profile)
        return profile

    def _persist(self, profile: UserProfile) -> None:
        try:
            data = profile.to_dict()
            data["preferences"] = json.dumps(data["preferences"])
            data["watchlist"] = json.dumps(data["watchlist"])
            with self.db._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_profiles
                    (id, name, profile_type, preferences, watchlist, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (data["id"], data["name"], data["profile_type"],
                      data["preferences"], data["watchlist"], data["created_at"]))
        except Exception as e:
            print(f"[ProfileRegistry] Persist error: {e}")

    def _load(self, profile_id: str) -> Optional[UserProfile]:
        try:
            with self.db._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM user_profiles WHERE id = ?", (profile_id,)
                ).fetchone()
                if row:
                    data = dict(row)
                    if data.get("preferences"):
                        data["preferences"] = json.loads(data["preferences"])
                    if data.get("watchlist"):
                        data["watchlist"] = json.loads(data["watchlist"])
                    profile = UserProfile.from_dict(data)
                    self._cache[profile.id] = profile
                    return profile
        except Exception as e:
            print(f"[ProfileRegistry] Load error: {e}")
        return None
