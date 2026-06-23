"""Tests for OSIRIS Memory Layer"""
import pytest
from core.memory import ShortTermMemory, LongTermMemory, MemoryStore
import time


class TestShortTermMemory:
    def test_store_and_recall(self):
        mem = ShortTermMemory()
        mem.store("test_key", {"value": 42})
        result = mem.recall("test_key")
        assert result == {"value": 42}

    def test_expiry(self):
        mem = ShortTermMemory(ttl_seconds=1)
        mem.store("expire_key", "data")
        time.sleep(1.5)
        result = mem.recall("expire_key")
        assert result is None

    def test_search(self):
        mem = ShortTermMemory()
        mem.store("key1", {"content": "Bitcoin price surge"})
        mem.store("key2", {"content": "Ethereum upgrade"})
        results = mem.search("bitcoin")
        assert len(results) == 1
        assert results[0]["key"] == "key1"

    def test_max_size(self):
        mem = ShortTermMemory(max_size=3)
        for i in range(5):
            mem.store(f"key_{i}", i)
        assert mem.size() == 3


class TestLongTermMemory:
    def test_store_and_recall(self):
        mem = LongTermMemory()
        mem.store("lt_key", {"big": "data"}, tags=["important"])
        result = mem.recall("lt_key")
        assert result == {"big": "data"}

    def test_search_by_tag(self):
        mem = LongTermMemory()
        mem.store("a", "data a", tags=["crypto", "btc"])
        mem.store("b", "data b", tags=["crypto", "eth"])
        mem.store("c", "data c", tags=["macro"])
        results = mem.search_by_tag("crypto")
        assert len(results) == 2


class TestMemoryStore:
    def test_integration(self):
        store = MemoryStore()
        store.remember_event("evt_1", "news_agent", {"opinion": "buy"})
        store.remember_event("evt_1", "macro_agent", {"opinion": "hold"})

        context = store.get_event_context("evt_1")
        assert len(context) == 4  # 2 short + 2 long term

        stats = store.get_stats()
        assert stats["events_tracked"] == 1
        assert stats["short_term_size"] == 2
        assert stats["long_term_size"] == 2
