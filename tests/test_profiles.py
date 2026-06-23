"""Tests for OSIRIS User Profiles"""
import pytest
from core.profiles.models import (
    ProfileType, UserProfile, ProfileRegistry,
    TraderPreferences, EntrepreneurPreferences, CreatorPreferences,
)


class TestPreferences:
    def test_trader_defaults(self):
        prefs = TraderPreferences()
        assert prefs.markets == ["crypto", "stocks", "forex"]
        assert prefs.risk_tolerance == "medium"
        assert prefs.enabled is True

    def test_entrepreneur_defaults(self):
        prefs = EntrepreneurPreferences()
        assert "tech" in prefs.industries
        assert "ai" in prefs.industries

    def test_creator_defaults(self):
        prefs = CreatorPreferences()
        assert "youtube" in prefs.platforms
        assert prefs.monetization_goal == "growth"

    def test_profile_creation(self):
        prefs = TraderPreferences(risk_tolerance="high", min_conviction=70.0)
        profile = UserProfile(
            id="test_1", name="Test Trader",
            profile_type=ProfileType.TRADER, preferences=prefs,
        )
        assert profile.profile_type == ProfileType.TRADER
        assert profile.preferences.risk_tolerance == "high"

    def test_serialization(self):
        prefs = CreatorPreferences(platforms=["youtube", "tiktok"])
        profile = UserProfile(
            id="creator_1", name="Content Creator",
            profile_type=ProfileType.CREATOR, preferences=prefs,
            watchlist=["BTC", "ETH"],
        )
        data = profile.to_dict()
        assert data["profile_type"] == "creator"
        assert "youtube" in data["preferences"]["platforms"]

        restored = UserProfile.from_dict(data)
        assert restored.id == profile.id
        assert restored.profile_type == ProfileType.CREATOR
        assert restored.watchlist == ["BTC", "ETH"]

    def test_registry(self):
        registry = ProfileRegistry()
        profile = registry.create_default("Default Trader", ProfileType.TRADER)
        assert profile.id is not None
        assert profile.name == "Default Trader"

        loaded = registry.get(profile.id)
        assert loaded is not None
        assert loaded.profile_type == ProfileType.TRADER

    def test_registry_get_by_type(self):
        registry = ProfileRegistry()
        registry.create_default("Trader 1", ProfileType.TRADER)
        registry.create_default("Trader 2", ProfileType.TRADER)
        registry.create_default("Creator 1", ProfileType.CREATOR)

        traders = registry.get_by_type(ProfileType.TRADER)
        creators = registry.get_by_type(ProfileType.CREATOR)
        assert len(traders) == 2
        assert len(creators) == 1
