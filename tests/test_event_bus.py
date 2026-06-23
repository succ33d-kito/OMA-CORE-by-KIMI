"""Tests for OSIRIS Event Bus"""
import pytest
from core.event_bus import EventBus, EventTopic


class TestEventBus:
    def test_publish_subscribe(self):
        bus = EventBus()
        received = []

        def callback(data):
            received.append(data)

        bus.subscribe(EventTopic.EVENTS_RAW, callback)
        bus.publish(EventTopic.EVENTS_RAW, {"test": "data"}, source="test")

        assert len(received) == 1
        assert received[0]["test"] == "data"

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        def callback(data):
            received.append(data)

        bus.subscribe(EventTopic.SYSTEM_ALERT, callback)
        bus.unsubscribe(EventTopic.SYSTEM_ALERT, callback)
        bus.publish(EventTopic.SYSTEM_ALERT, {"alert": "test"})

        assert len(received) == 0

    def test_multiple_subscribers(self):
        bus = EventBus()
        results = []

        def cb1(data):
            results.append("cb1")

        def cb2(data):
            results.append("cb2")

        bus.subscribe(EventTopic.EVENTS_RAW, cb1)
        bus.subscribe(EventTopic.EVENTS_RAW, cb2)
        bus.publish(EventTopic.EVENTS_RAW, {})

        assert len(results) == 2
        assert "cb1" in results
        assert "cb2" in results

    def test_history(self):
        bus = EventBus()
        bus.publish(EventTopic.EVENTS_RAW, {"id": 1}, source="src1")
        bus.publish(EventTopic.OPINIONS_AGENT, {"id": 2}, source="src2")

        history = bus.get_history(limit=10)
        assert len(history) == 2
        assert history[0]["topic"] == "events.raw"
        assert history[1]["topic"] == "opinions.agent"

    def test_history_filter_by_topic(self):
        bus = EventBus()
        bus.publish(EventTopic.EVENTS_RAW, {}, source="a")
        bus.publish(EventTopic.SYSTEM_ALERT, {}, source="b")

        filtered = bus.get_history(topic=EventTopic.SYSTEM_ALERT)
        assert len(filtered) == 1
        assert filtered[0]["topic"] == "system.alert"

    def test_clear_history(self):
        bus = EventBus()
        bus.publish(EventTopic.EVENTS_RAW, {})
        bus.clear_history()
        assert len(bus.get_history()) == 0
