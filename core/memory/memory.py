"""OSIRIS Memory Layer — Short-term, long-term, and persistent memory"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json


class ShortTermMemory:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._store: Dict[str, dict] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def store(self, key: str, data: Any, metadata: Optional[dict] = None) -> None:
        entry = {
            "key": key,
            "data": data,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._store[key] = entry
        if len(self._store) > self._max_size:
            oldest = min(self._store.keys(), key=lambda k: self._store[k]["timestamp"])
            del self._store[oldest]

    def recall(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        age = datetime.now(timezone.utc) - datetime.fromisoformat(entry["timestamp"])
        if age.total_seconds() > self._ttl:
            del self._store[key]
            return None
        return entry["data"]

    def search(self, query: str, top_k: int = 10) -> List[dict]:
        query_lower = query.lower()
        results = []
        for entry in self._store.values():
            data_str = json.dumps(entry["data"]).lower()
            if query_lower in data_str:
                results.append(entry)
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)[:top_k]

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)


class LongTermMemory:
    def __init__(self, db=None):
        self._store: Dict[str, dict] = {}
        self.db = db

    def store(self, key: str, data: Any, tags: Optional[List[str]] = None) -> None:
        entry = {
            "key": key,
            "data": data,
            "tags": tags or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "access_count": 0,
        }
        self._store[key] = entry

    def recall(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry:
            entry["access_count"] += 1
            return entry["data"]
        return None

    def search_by_tag(self, tag: str) -> List[dict]:
        return [
            entry for entry in self._store.values()
            if tag in entry["tags"]
        ]

    def search(self, query: str, top_k: int = 10) -> List[dict]:
        query_lower = query.lower()
        results = []
        for entry in self._store.values():
            data_str = json.dumps(entry["data"]).lower()
            tag_str = " ".join(entry["tags"]).lower()
            if query_lower in data_str or query_lower in tag_str:
                results.append(entry)
        return sorted(results, key=lambda x: (x["access_count"], x["timestamp"]), reverse=True)[:top_k]

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)


class MemoryStore:
    def __init__(self, db=None):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(db)
        self._event_memory: Dict[str, List[str]] = defaultdict(list)

    def remember_event(self, event_id: str, agent_name: str, opinion_data: dict) -> None:
        self._event_memory[event_id].append(agent_name)
        self.short_term.store(f"opinion:{event_id}:{agent_name}", opinion_data)
        self.long_term.store(
            f"event:{event_id}:{agent_name}",
            opinion_data,
            tags=["opinion", event_id[:8], agent_name],
        )

    def get_event_context(self, event_id: str) -> List[dict]:
        results = []
        for key, entry in self.long_term._store.items():
            if event_id[:8] in key or event_id in key:
                results.append(entry)
        for key, entry in self.short_term._store.items():
            if event_id[:8] in key or event_id in key:
                results.append(entry)
        return results

    def get_stats(self) -> dict:
        return {
            "short_term_size": self.short_term.size(),
            "long_term_size": self.long_term.size(),
            "events_tracked": len(self._event_memory),
        }
