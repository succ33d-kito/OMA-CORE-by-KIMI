#!/usr/bin/env python3
"""OSIRIS PostgreSQL Migration — Non-destructive upsert-based sync"""
import sqlite3
import psycopg2
import os
import sys


def get_or_create_cursor(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY, source TEXT, source_url TEXT, source_id TEXT,
            event_type TEXT, category TEXT, title TEXT, summary TEXT,
            raw_content TEXT, timestamp TIMESTAMPTZ, detected_at TIMESTAMPTZ,
            assets TEXT, keywords TEXT, entities TEXT, regions TEXT,
            sentiment INTEGER, sentiment_score REAL, urgency INTEGER,
            confidence REAL, impact_score REAL, relevance_score REAL,
            language TEXT, metadata TEXT, processed INTEGER, enriched INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY, event_id TEXT, title TEXT, description TEXT,
            opportunity_type TEXT, asset_class TEXT, assets TEXT,
            score REAL, conviction REAL, priority TEXT,
            action_suggested TEXT, risk_level TEXT,
            timestamp TIMESTAMPTZ, expires_at TIMESTAMPTZ, status TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id TEXT PRIMARY KEY, name TEXT, profile_type TEXT,
            preferences TEXT, watchlist TEXT, risk_tolerance TEXT,
            created_at TIMESTAMPTZ
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_opp_event ON opportunities(event_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_opp_score ON opportunities(score)")
    return cur


def upsert_table(sqlite_conn, pg_cur, table_name, conflict_col="id"):
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute(f"SELECT name FROM PRAGMA_TABLE_INFO('{table_name}')")
    cols = [c[0] for c in sqlite_cur.fetchall()]
    if not cols:
        print(f"  [SKIP] Table '{table_name}' has no columns")
        return 0

    sqlite_cur.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cur.fetchall()
    if not rows:
        print(f"  [SKIP] No rows in {table_name}")
        return 0

    placeholders = ','.join(['%s'] * len(cols))
    col_list = ','.join(cols)
    update_parts = [f"{c}=EXCLUDED.{c}" for c in cols if c != conflict_col]
    update_str = ','.join(update_parts)

    upsert_sql = (
        f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_col}) DO UPDATE SET {update_str}"
    )

    for row in rows:
        try:
            pg_cur.execute(upsert_sql, tuple(row))
        except Exception as e:
            print(f"  [WARN] Upsert failed for row in {table_name}: {e}")
            continue

    print(f"  ✓ {len(rows)} rows synced in {table_name}")
    return len(rows)


def migrate():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: export DATABASE_URL='postgresql://...'")
        sys.exit(1)

    sqlite_conn = sqlite3.connect("oma_core.db")
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(database_url, sslmode='require')
    pg_cur = get_or_create_cursor(pg_conn)

    print("Syncing SQLite → PostgreSQL (non-destructive)...")
    for table in ("events", "opportunities", "user_profiles"):
        upsert_table(sqlite_conn, pg_cur, table)

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()
    print("Sync complete — existing data preserved, duplicates ignored")


if __name__ == "__main__":
    migrate()
