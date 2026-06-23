"""OSIRIS Event Bus — Decoupled pub/sub message bus"""
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import inspect
import logging

logger = logging.getLogger("oma-core.event-bus")


class EventTopic(Enum):
    EVENTS_RAW = "events.raw"
    EVENTS_PROCESSED = "events.processed"
    OPINIONS_AGENT = "opinions.agent"
    DECISIONS_COUNCIL = "decisions.council"
    OPPORTUNITIES_GENERATED = "opportunities.generated"
    WORLD_MONITOR_TICK = "world_monitor.tick"
    MEMORY_STORE = "memory.store"
    MEMORY_RECALL = "memory.recall"
    SYSTEM_ALERT = "system.alert"
    ACTION_TRIGGERED = "action.triggered"


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {topic.value: [] for topic in EventTopic}
        self._history: List[dict] = []
        self._max_history = 1000

    def subscribe(self, topic: EventTopic, callback: Callable) -> None:
        topic_key = topic.value
        if topic_key not in self._subscribers:
            self._subscribers[topic_key] = []
        self._subscribers[topic_key].append(callback)
        logger.debug(f"[EventBus] Subscribed {callback.__name__} to {topic_key}")

    def unsubscribe(self, topic: EventTopic, callback: Callable) -> None:
        topic_key = topic.value
        if topic_key in self._subscribers:
            self._subscribers[topic_key] = [cb for cb in self._subscribers[topic_key] if cb is not callback]
            logger.debug(f"[EventBus] Unsubscribed {callback.__name__} from {topic_key}")

    def publish(self, topic: EventTopic, data: Any, source: Optional[str] = None) -> None:
        topic_key = topic.value
        message = {
            "topic": topic_key,
            "data": data,
            "source": source or "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        if topic_key in self._subscribers:
            for callback in self._subscribers[topic_key]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        logger.warning(f"[EventBus] Async callback {callback.__name__} not supported yet")
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"[EventBus] Error in {callback.__name__}: {e}")

    def get_history(self, topic: Optional[EventTopic] = None, limit: int = 50) -> List[dict]:
        if topic:
            return [m for m in self._history[-limit:] if m["topic"] == topic.value]
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()


bus = EventBus()
