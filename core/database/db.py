"""O.M.A.-C.O.R.E. Database Layer"""
import sqlite3, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from core.schemas.event_schema import Event, EVENT_TABLE_SCHEMA

class OMACoreDatabase:
    def __init__(self, db_path="oma_core.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        with self._get_connection() as conn:
            conn.executescript(EVENT_TABLE_SCHEMA)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY, event_id TEXT NOT NULL, title TEXT NOT NULL,
                    description TEXT, opportunity_type TEXT NOT NULL, asset_class TEXT,
                    assets TEXT, score REAL, conviction REAL, priority TEXT,
                    action_suggested TEXT, risk_level TEXT, timestamp TEXT NOT NULL,
                    expires_at TEXT, status TEXT DEFAULT 'active',
                    FOREIGN KEY (event_id) REFERENCES events(id)
                );
                CREATE INDEX IF NOT EXISTS idx_opp_event ON opportunities(event_id);
                CREATE INDEX IF NOT EXISTS idx_opp_score ON opportunities(score);
                CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status);
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY, name TEXT, profile_type TEXT NOT NULL,
                    preferences TEXT, watchlist TEXT, risk_tolerance TEXT, created_at TEXT NOT NULL
                );
            """)
    
    def insert_event(self, event: Event) -> str:
        data = event.to_dict()
        for field in ["assets", "keywords", "entities", "regions"]:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field])
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO events 
                (id, source, source_url, source_id, event_type, category, title, summary,
                 raw_content, timestamp, detected_at, assets, keywords, entities, regions,
                 sentiment, sentiment_score, urgency, confidence, impact_score, relevance_score,
                 language, metadata, processed, enriched)
                VALUES (:id, :source, :source_url, :source_id, :event_type, :category, :title,
                 :summary, :raw_content, :timestamp, :detected_at, :assets, :keywords,
                 :entities, :regions, :sentiment, :sentiment_score, :urgency, :confidence,
                 :impact_score, :relevance_score, :language, :metadata, :processed, :enriched)
            """, data)
        return event.id
    
    def get_unprocessed_events(self, limit=100):
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE processed = 0 ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
    
    def get_recent_events(self, hours=24, limit=50):
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM events WHERE timestamp > datetime('now', '-{} hours')
                   ORDER BY urgency DESC, timestamp DESC LIMIT ?""".format(hours),
                (limit,)
            ).fetchall()
            return [self._row_to_event(row) for row in rows]
    
    def mark_processed(self, event_id):
        with self._get_connection() as conn:
            conn.execute("UPDATE events SET processed = 1 WHERE id = ?", (event_id,))
    
    def update_event_scores(self, event_id, impact, relevance):
        with self._get_connection() as conn:
            conn.execute("UPDATE events SET impact_score = ?, relevance_score = ? WHERE id = ?",
                        (impact, relevance, event_id))
    
    def get_event_stats(self):
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            unprocessed = conn.execute("SELECT COUNT(*) FROM events WHERE processed = 0").fetchone()[0]
            by_type = conn.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type").fetchall()
            by_urgency = conn.execute("SELECT urgency, COUNT(*) FROM events GROUP BY urgency").fetchall()
            return {
                "total_events": total, "unprocessed": unprocessed,
                "by_type": {row[0]: row[1] for row in by_type},
                "by_urgency": {row[0]: row[1] for row in by_urgency}
            }
    
    def _row_to_event(self, row):
        data = dict(row)
        for field in ["assets", "keywords", "entities", "regions"]:
            if data.get(field):
                try: data[field] = json.loads(data[field])
                except: data[field] = []
            else: data[field] = []
        if data.get("metadata"):
            try: data["metadata"] = json.loads(data["metadata"])
            except: data["metadata"] = {}
        return Event.from_dict(data)
    
    def insert_opportunity(self, opportunity):
        opp_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO opportunities 
                (id, event_id, title, description, opportunity_type, asset_class,
                 assets, score, conviction, priority, action_suggested, risk_level,
                 timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (opp_id, opportunity.get("event_id"), opportunity.get("title", ""),
                  opportunity.get("description", ""), opportunity.get("opportunity_type", ""),
                  opportunity.get("asset_class", ""), json.dumps(opportunity.get("assets", [])),
                  opportunity.get("score", 0.0), opportunity.get("conviction", 0.0),
                  opportunity.get("priority", "low"), opportunity.get("action_suggested", ""),
                  opportunity.get("risk_level", "medium"),
                  datetime.now(timezone.utc).isoformat(), "active"))
        return opp_id
    
    def get_active_opportunities(self, limit=50):
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT o.*, e.title as event_title, e.source, e.event_type
                   FROM opportunities o JOIN events e ON o.event_id = e.id
                   WHERE o.status = 'active'
                   ORDER BY o.score DESC, o.conviction DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

db = OMACoreDatabase()
