#!/usr/bin/env python3
"""OMA-CORE Dashboard - PostgreSQL version for Render"""

import os
import psycopg2
import json
from datetime import datetime, timezone
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def api_data():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM opportunities WHERE timestamp >= NOW() - INTERVAL '168 hours' AND status = 'active' ORDER BY score DESC LIMIT 100")
        columns = [desc[0] for desc in cur.description]
        opportunities = []
        for row in cur.fetchall():
            opp = dict(zip(columns, row))
            if isinstance(opp.get('assets'), str):
                try: opp['assets'] = json.loads(opp['assets'])
                except: opp['assets'] = [opp['assets']]
            if isinstance(opp.get('action_details'), str):
                try: opp['action_details'] = json.loads(opp['action_details'])
                except: opp['action_details'] = {"timeframe": "N/A", "rationale": ""}
            opportunities.append(opp)
        cur.execute("SELECT COUNT(*) FROM events")
        total_events = cur.fetchone()[0]
        cur.execute("SELECT priority, COUNT(*) FROM opportunities WHERE timestamp >= NOW() - INTERVAL '168 hours' GROUP BY priority")
        by_priority = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "count": len(opportunities), "total_events": total_events, "by_priority": by_priority, "opportunities": opportunities})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

HTML_TEMPLATE = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>OMA-CORE Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}.header{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:20px 40px;border-bottom:2px solid #00d4ff;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px}.header h1{color:#00d4ff;font-size:28px;letter-spacing:2px}.header .status{display:flex;gap:20px;align-items:center;flex-wrap:wrap}.status-item{background:rgba(0,212,255,0.1);padding:10px 20px;border-radius:8px;border:1px solid rgba(0,212,255,0.3)}.status-item .label{font-size:12px;color:#888}.status-item .value{font-size:20px;font-weight:bold;color:#00d4ff}.container{max-width:1400px;margin:0 auto;padding:30px}.filters{display:flex;gap:15px;margin-bottom:25px;flex-wrap:wrap}.filter-btn{background:#1a1a2e;border:1px solid #333;color:#e0e0e0;padding:10px 20px;border-radius:6px;cursor:pointer;transition:all 0.3s}.filter-btn:hover,.filter-btn.active{background:#00d4ff;color:#0a0a0f;border-color:#00d4ff}.opportunities-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:20px}.opp-card{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);border-radius:12px;padding:20px;border-left:4px solid;transition:transform 0.2s,box-shadow 0.2s}.opp-card:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,212,255,0.1)}.opp-card.CRITICAL{border-left-color:#ff0040}.opp-card.HIGH{border-left-color:#ffaa00}.opp-card.MEDIUM{border-left-color:#00d4ff}.opp-card.LOW{border-left-color:#00ff88}.opp-header{display:flex;justify-content:space-between;align-items:start;margin-bottom:15px;gap:10px}.opp-title{font-size:16px;font-weight:600;color:#fff;line-height:1.4;flex:1}.opp-priority{padding:4px 12px;border-radius:4px;font-size:12px;font-weight:bold;text-transform:uppercase;white-space:nowrap}.priority-CRITICAL{background:#ff0040;color:#fff}.priority-HIGH{background:#ffaa00;color:#000}.priority-MEDIUM{background:#00d4ff;color:#000}.priority-LOW{background:#00ff88;color:#000}.opp-meta{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:15px}.meta-item{display:flex;align-items:center;gap:8px;font-size:13px}.meta-item .label{color:#888}.meta-item .value{color:#e0e0e0;font-weight:500}.opp-score-bar{background:rgba(255,255,255,0.05);height:6px;border-radius:3px;margin-bottom:15px;overflow:hidden}.opp-score-fill{height:100%;border-radius:3px;transition:width 0.5s}.score-high{background:linear-gradient(90deg,#00ff88,#00d4ff)}.score-mid{background:linear-gradient(90deg,#ffaa00,#ff0040)}.score-low{background:#ff0040}.opp-action{background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);padding:12px;border-radius:8px;margin-top:10px}.opp-action .action-title{color:#00d4ff;font-size:13px;font-weight:600;margin-bottom:5px}.opp-action .action-text{font-size:13px;color:#ccc;line-height:1.5}.loading{text-align:center;padding:50px;color:#888}.error-box{color:#ff0040;text-align:center;padding:50px;background:rgba(255,0,64,0.05);border-radius:12px;border:1px solid rgba(255,0,64,0.2)}.empty-box{text-align:center;padding:50px;color:#888}.timestamp{text-align:center;color:#666;font-size:12px;margin-top:30px;padding-bottom:30px}.live-indicator{display:inline-block;width:8px;height:8px;background:#00ff88;border-radius:50%;margin-right:8px;animation:pulse 2s infinite}@keyframes pulse{0%{opacity:1}50%{opacity:0.5}100%{opacity:1}}@media(max-width:768px){.opportunities-grid{grid-template-columns:1fr}.header{padding:15px 20px}.header h1{font-size:20px}}</style></head><body><div class="header"><h1><span class="live-indicator"></span>OMA-CORE v2.1</h1><div class="status"><div class="status-item"><div class="label">Oportunidades</div><div class="value" id="total-opps">--</div></div><div class="status-item"><div class="label">Eventos</div><div class="value" id="total-events">--</div></div><div class="status-item"><div class="label">Critical</div><div class="value" id="critical-count">--</div></div></div></div><div class="container"><div class="filters"><button class="filter-btn active" onclick="filterBy('all')">Todas</button><button class="filter-btn" onclick="filterBy('CRITICAL')">Critical</button><button class="filter-btn" onclick="filterBy('HIGH')">High</button><button class="filter-btn" onclick="filterBy('MEDIUM')">Medium</button><button class="filter-btn" onclick="filterBy('LOW')">Low</button></div><div id="opportunities" class="opportunities-grid"><div class="loading">Cargando...</div></div><div class="timestamp" id="timestamp"></div></div><script>let allOpportunities=[];function formatAssets(a){if(!a)return'N/A';if(typeof a==='string'){try{const p=JSON.parse(a);if(Array.isArray(p))return p.join(', ');return a}catch{return a}}if(Array.isArray(a))return a.join(', ');return String(a)}async function loadData(){try{const r=await fetch('/api/data');const d=await r.json();if(d.status==='ok'){allOpportunities=d.opportunities;renderOpportunities(allOpportunities);updateStats(d);document.getElementById('timestamp').textContent='Actualizado: '+new Date(d.timestamp).toLocaleString('es-ES')}}catch(e){document.getElementById('opportunities').innerHTML='<div class="error-box">Error: '+e.message+'</div>'}}function renderOpportunities(opps){const c=document.getElementById('opportunities');if(opps.length===0){c.innerHTML='<div class="empty-box">No hay oportunidades activas</div>';return}c.innerHTML=opps.map(opp=>{const sc=opp.score>=80?'score-high':opp.score>=50?'score-mid':'score-low';const re=opp.risk_level==='VERY_HIGH'?'!!':opp.risk_level==='HIGH'?'!':opp.risk_level==='MEDIUM'?'~':'OK';return'<div class="opp-card '+opp.priority+'"><div class="opp-header"><div class="opp-title">'+escapeHtml(opp.title)+'</div><span class="opp-priority priority-'+opp.priority+'">'+opp.priority+'</span></div><div class="opp-score-bar"><div class="opp-score-fill '+sc+'" style="width:'+opp.score+'%"></div></div><div class="opp-meta"><div class="meta-item"><span class="label">Score:</span><span class="value">'+opp.score+'/100</span></div><div class="meta-item"><span class="label">Conviccion:</span><span class="value">'+opp.conviction+'/100</span></div><div class="meta-item"><span class="label">Assets:</span><span class="value">'+formatAssets(opp.assets)+'</span></div><div class="meta-item"><span class="label">Riesgo:</span><span class="value">'+re+' '+opp.risk_level+'</span></div><div class="meta-item"><span class="label">Fuente:</span><span class="value">'+opp.source+'</span></div><div class="meta-item"><span class="label">Timeframe:</span><span class="value">'+(opp.action_details?.timeframe||'N/A')+'</span></div></div><div class="opp-action"><div class="action-title">Accion sugerida</div><div class="action-text">'+escapeHtml(opp.action_suggested)+'</div><div class="action-text" style="margin-top:5px;color:#888;font-size:12px;">'+escapeHtml(opp.action_details?.rationale||'')+'</div></div></div>'}).join('')}function filterBy(priority){document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');if(priority==='all'){renderOpportunities(allOpportunities)}else{renderOpportunities(allOpportunities.filter(o=>o.priority===priority))}}function updateStats(d){document.getElementById('total-opps').textContent=d.count;document.getElementById('total-events').textContent=d.total_events||'--';document.getElementById('critical-count').textContent=(d.by_priority&&d.by_priority.CRITICAL)||0}function escapeHtml(t){if(!t)return'';const d=document.createElement('div');d.textContent=t;return d.innerHTML}loadData();setInterval(loadData,30000)</script></body></html>"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"OMA-CORE Dashboard running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
