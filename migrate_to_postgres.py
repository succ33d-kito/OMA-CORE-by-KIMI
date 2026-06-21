#!/usr/bin/env python3
import sqlite3
import psycopg2
import os
import sys

def migrate():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: export DATABASE_URL='tu-url-aqui'")
        sys.exit(1)
    
    # Conectar SQLite
    sqlite_conn = sqlite3.connect("oma_core.db")
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    # Conectar PostgreSQL
    pg_conn = psycopg2.connect(database_url, sslmode='require')
    pg_cur = pg_conn.cursor()
    
    # Crear tablas
    print("Creando tablas en PostgreSQL...")
    pg_cur.execute("DROP TABLE IF EXISTS opportunities, user_profiles, events CASCADE")
    
    pg_cur.execute("""
        CREATE TABLE events (
            id TEXT PRIMARY KEY, source TEXT, source_url TEXT, source_id TEXT,
            event_type TEXT, category TEXT, title TEXT, summary TEXT,
            raw_content TEXT, timestamp TIMESTAMPTZ, detected_at TIMESTAMPTZ,
            assets TEXT, keywords TEXT, entities TEXT, regions TEXT,
            sentiment INTEGER, sentiment_score REAL, urgency INTEGER,
            confidence REAL, impact_score REAL, relevance_score REAL,
            language TEXT, metadata TEXT, processed INTEGER, enriched INTEGER
        )
    """)
    pg_cur.execute("CREATE INDEX idx_events_timestamp ON events(timestamp)")
    pg_cur.execute("CREATE INDEX idx_events_source ON events(source)")
    pg_cur.execute("CREATE INDEX idx_events_type ON events(event_type)")
    
    pg_cur.execute("""
        CREATE TABLE opportunities (
            id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
            opportunity_type TEXT, asset_class TEXT, assets TEXT,
            score REAL, conviction REAL, priority TEXT,
            action_suggested TEXT, risk_level TEXT,
            timestamp TIMESTAMPTZ, expires_at TIMESTAMPTZ, status TEXT
        )
    """)
    pg_cur.execute("CREATE INDEX idx_opp_event ON opportunities(event_id)")
    pg_cur.execute("CREATE INDEX idx_opp_score ON opportunities(score)")
    
    pg_cur.execute("""
        CREATE TABLE user_profiles (
            id TEXT PRIMARY KEY, name TEXT, profile_type TEXT,
            preferences TEXT, watchlist TEXT, risk_tolerance TEXT,
            created_at TIMESTAMPTZ
        )
    """)
    
    # Migrar events
    print("Migrando events...")
    sqlite_cur.execute("SELECT * FROM events")
    events = sqlite_cur.fetchall()
    for row in events:
        sqlite_cur.execute("SELECT name FROM PRAGMA_TABLE_INFO('events')")
        cols = [c[0] for c in sqlite_cur.fetchall()]
        placeholders = ','.join(['%s'] * len(cols))
        pg_cur.execute(f"INSERT INTO events ({','.join(cols)}) VALUES ({placeholders})", tuple(row))
    
    # Migrar opportunities
    print("Migrando opportunities...")
    sqlite_cur.execute("SELECT * FROM opportunities")
    opps = sqlite_cur.fetchall()
    for row in opps:
        sqlite_cur.execute("SELECT name FROM PRAGMA_TABLE_INFO('opportunities')")
        cols = [c[0] for c in sqlite_cur.fetchall()]
        placeholders = ','.join(['%s'] * len(cols))
        pg_cur.execute(f"INSERT INTO opportunities ({','.join(cols)}) VALUES ({placeholders})", tuple(row))
    
    # Migrar user_profiles
    print("Migrando user_profiles...")
    sqlite_cur.execute("SELECT * FROM user_profiles")
    profiles = sqlite_cur.fetchall()
    for row in profiles:
        sqlite_cur.execute("SELECT name FROM PRAGMA_TABLE_INFO('user_profiles')")
        cols = [c[0] for c in sqlite_cur.fetchall()]
        placeholders = ','.join(['%s'] * len(cols))
        pg_cur.execute(f"INSERT INTO user_profiles ({','.join(cols)}) VALUES ({placeholders})", tuple(row))
    
    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()
    
    print(f"✅ Migracion completada!")
    print(f"   Events: {len(events)}")
    print(f"   Opportunities: {len(opps)}")
    print(f"   Profiles: {len(profiles)}")

if __name__ == "__main__":
    migrate()
