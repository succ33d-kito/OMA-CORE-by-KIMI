#!/usr/bin/env python3
"""
Exportador de datos para GitHub Pages
Genera docs/data.json desde la base de datos SQLite
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

def export_for_github(db_path="oma_core.db", output_dir="docs"):
    """Exporta oportunidades y stats a JSON para GitHub Pages."""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Exportar oportunidades activas (ultimas 168h)
    cursor.execute("""
        SELECT * FROM opportunities 
        WHERE timestamp >= datetime('now', '-168 hours')
        AND status = 'active'
        ORDER BY score DESC
        LIMIT 100
    """)
    
    opportunities = []
    for row in cursor.fetchall():
        opp = dict(row)
        if isinstance(opp.get('assets'), str):
            try:
                opp['assets'] = json.loads(opp['assets'])
            except:
                opp['assets'] = [opp['assets']]
        if isinstance(opp.get('action_details'), str):
            try:
                opp['action_details'] = json.loads(opp['action_details'])
            except:
                opp['action_details'] = {"timeframe": "N/A", "rationale": ""}
        opportunities.append(opp)
    
    cursor.execute("SELECT COUNT(*) as total FROM events")
    total_events = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT priority, COUNT(*) as count 
        FROM opportunities 
        WHERE timestamp >= datetime('now', '-168 hours')
        GROUP BY priority
    """)
    by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}
    
    data = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(opportunities),
        "total_events": total_events,
        "by_priority": by_priority,
        "opportunities": opportunities
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, "data.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    conn.close()
    
    print(f"Exportado: {json_path}")
    print(f"   Oportunidades: {len(opportunities)}")
    print(f"   Eventos totales: {total_events}")
    print(f"   Por prioridad: {by_priority}")

if __name__ == "__main__":
    export_for_github()
