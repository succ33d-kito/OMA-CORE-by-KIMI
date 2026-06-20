"""O.M.A.-C.O.R.E. Web Dashboard"""
import os
import sys
import json
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify

# Añadir el directorio padre al path para importar core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.database.db import OMACoreDatabase

app = Flask(__name__)
db = OMACoreDatabase(os.path.join(os.path.dirname(__file__), '..', 'oma_core.db'))

@app.route('/')
def index():
    """Página principal del dashboard."""
    return render_template('index.html')

@app.route('/api/opportunities')
def api_opportunities():
    """API: Retorna oportunidades activas en JSON."""
    try:
        opps = db.get_active_opportunities(limit=100)
        return jsonify({
            "status": "ok",
            "count": len(opps),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunities": opps
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API: Retorna estadísticas del sistema."""
    try:
        stats = db.get_event_stats()
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": stats
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/events')
def api_events():
    """API: Retorna eventos recientes."""
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 50))
        events = db.get_recent_events(hours=hours, limit=limit)
        return jsonify({
            "status": "ok",
            "count": len(events),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "events": events
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 OMA-CORE Dashboard")
    print("=" * 50)
    print("Abre tu navegador en: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
