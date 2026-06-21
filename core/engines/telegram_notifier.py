"""
O.M.A.-C.O.R.E. Telegram Notifier v2.2
Notificaciones para oma run con resumen completo
"""

import os
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

class TelegramNotifier:
    """Envia notificaciones de alertas y resumenes a Telegram."""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        self.api_base = f"https://api.telegram.org/bot{self.token}" if self.token else None
        self._last_critical_alert = None
        self._alert_cooldown_hours = 4

    def _can_send_critical(self) -> bool:
        if self._last_critical_alert is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self._last_critical_alert).total_seconds() / 3600
        return elapsed >= self._alert_cooldown_hours

    def _mark_critical_sent(self):
        self._last_critical_alert = datetime.now(timezone.utc)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled:
            print("[Telegram] Notificaciones desactivadas (verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID)")
            return False
        try:
            url = f"{self.api_base}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print("[Telegram] ✅ Mensaje enviado")
            return True
        except Exception as e:
            print(f"[Telegram] ❌ Error: {e}")
            return False

    def send_run_summary(self, opportunities: List[Dict[str, Any]], stats: Dict[str, Any]) -> bool:
        """
        Envia resumen completo de 'oma run'.
        Incluye todas las prioridades (CRITICAL, HIGH, MEDIUM, LOW).
        """
        if not self.enabled:
            return False
        
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        total = len(opportunities)
        
        # Contar por prioridad
        critical = [o for o in opportunities if o.get("priority") == "CRITICAL"]
        high = [o for o in opportunities if o.get("priority") == "HIGH"]
        medium = [o for o in opportunities if o.get("priority") == "MEDIUM"]
        low = [o for o in opportunities if o.get("priority") == "LOW"]
        
        # Emojis
        type_emojis = {
            "LONG_SETUP": "🟢📈", "SHORT_SETUP": "🔴📉", "MOMENTUM_PLAY": "🚀",
            "AVOID_OR_SHORT": "⚠️🚫", "SAFE_HAVEN_FLOW": "🛡️", "RISK_OFF": "📉🔻",
            "WHALE_ACCUMULATION": "🐋🟢", "WHALE_DISTRIBUTION": "🐋🔻", "VIRAL_MOMENTUM": "🔥",
            "POST_EARNINGS_RUN": "📊", "MACRO_TAILWIND": "📈🌬️", "MACRO_HEADWIND": "📉🌬️",
            "REGULATORY_TAILWIND": "✅📋", "REGULATORY_HEADWIND": "🚫📋",
            "SENTIMENT_TURN_BULL": "😀📈", "SENTIMENT_TURN_BEAR": "😰📉", "ARB_OPPORTUNITY": "💰",
            "WATCHLIST_ADD": "👁️", "NEWS_DRIVEN": "📰",
            "TECHNICAL_BREAKOUT": "📈🔨", "TECHNICAL_BREAKDOWN": "📉🔨", "TECHNICAL_WATCH": "👁️📊",
            "WHALE_WATCH": "🐋👁️", "MONITOR_COMPLIANCE": "📋👁️", "MONITOR_GEO": "🌍👁️",
            "MONITOR_MACRO": "📊👁️", "EARNINGS_NEUTRAL": "📊", "SENTIMENT_WATCH": "👁️📊",
        }
        
        lines = [
            f"<b>🤖 OMA-CORE RUN COMPLETADO</b>",
            f"<b>📅 {now} UTC</b>",
            f"",
            f"<b>📊 RESUMEN</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━━",
            f"<b>🚨 CRITICAL:</b> {len(critical)}",
            f"<b>🔥 HIGH:</b> {len(high)}",
            f"<b>💡 MEDIUM:</b> {len(medium)}",
            f"<b>📋 LOW:</b> {len(low)}",
            f"<b>📈 TOTAL:</b> {total}",
            f"",
        ]
        
        # Stats del pipeline
        if stats:
            lines.append(f"<b>⚙️ PIPELINE</b>")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"<b>📥 Eventos procesados:</b> {stats.get('events_processed', 'N/A')}")
            lines.append(f"<b>💾 Eventos almacenados:</b> {stats.get('events_stored', 'N/A')}")
            lines.append(f"<b>🎯 Oportunidades generadas:</b> {stats.get('opportunities_generated', 'N/A')}")
            lines.append(f"")
        
        # Top 5 oportunidades (mejores scores)
        if opportunities:
            top_opps = sorted(opportunities, key=lambda x: x.get("score", 0), reverse=True)[:5]
            lines.append(f"<b>🏆 TOP 5 OPORTUNIDADES</b>")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━")
            
            for i, opp in enumerate(top_opps, 1):
                opp_type = opp.get("opportunity_type", "UNKNOWN")
                emoji = type_emojis.get(opp_type, "📌")
                priority = opp.get("priority", "LOW")
                score = opp.get("score", 0)
                assets = ", ".join(opp.get("assets", [])) or "N/A"
                action = opp.get("action_suggested", "N/A")[:50]
                
                lines.append(f"")
                lines.append(f"<b>#{i} {emoji} {opp_type}</b>")
                lines.append(f"<b>Prioridad:</b> {priority}")
                lines.append(f"<b>Score:</b> {score}/100")
                lines.append(f"<b>Assets:</b> {assets}")
                lines.append(f"<b>Accion:</b> {action}")
        
        lines.append(f"")
        lines.append(f"<b>━━━━━━━━━━━━━━━━━━━━━━━</b>")
        lines.append(f"<i>Dashboard: https://oma-core-by-kimi.onrender.com</i>")
        
        message = "\n".join(lines)
        return self.send_message(message)

    def send_critical_alert(self, opportunities: List[Dict[str, Any]]) -> bool:
        """
        Envia alerta CRITICAL (con cooldown de 4h).
        Solo para oportunidades CRITICAL.
        """
        if not self.enabled or not opportunities:
            return False
        
        critical = [o for o in opportunities if o.get("priority") == "CRITICAL"]
        if not critical:
            return False
        
        if not self._can_send_critical():
            hours_since = (datetime.now(timezone.utc) - self._last_critical_alert).total_seconds() / 3600
            print(f"[Telegram] ⏳ Cooldown activo ({hours_since:.1f}h / {self._alert_cooldown_hours}h)")
            return False
        
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        lines = [
            f"<b>🚨 ALERTA CRITICAL - OMA-CORE</b>",
            f"<b>📅 {now} UTC</b>",
            f"",
            f"<b>Se detectaron {len(critical)} oportunidades CRITICAL</b>",
            f"<b>Proxima alerta: En ~4 horas</b>",
            f"",
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━</b>",
        ]
        
        for i, opp in enumerate(critical[:5], 1):
            opp_type = opp.get("opportunity_type", "UNKNOWN")
            score = opp.get("score", 0)
            assets = ", ".join(opp.get("assets", [])) or "N/A"
            action = opp.get("action_suggested", "N/A")[:50]
            
            lines.append(f"")
            lines.append(f"<b>#{i} {opp_type}</b>")
            lines.append(f"<b>Score:</b> {score}/100")
            lines.append(f"<b>Assets:</b> {assets}")
            lines.append(f"<b>Accion:</b> {action}")
        
        lines.append(f"")
        lines.append(f"<b>━━━━━━━━━━━━━━━━━━━━━━━</b>")
        lines.append(f"<i>Dashboard: https://oma-core-by-kimi.onrender.com</i>")
        
        message = "\n".join(lines)
        
        success = self.send_message(message)
        if success:
            self._mark_critical_sent()
        return success

    def test_connection(self) -> bool:
        if not self.enabled:
            print("[Telegram] ❌ Notificaciones desactivadas (verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID)")
            return False
        try:
            url = f"{self.api_base}/getMe"
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("ok"):
                bot_name = data["result"].get("username", "Unknown")
                print(f"[Telegram] ✅ Conectado como @{bot_name}")
                return True
            else:
                print(f"[Telegram] ❌ Error: {data.get('description')}")
                return False
        except Exception as e:
            print(f"[Telegram] ❌ Error: {e}")
            return False
