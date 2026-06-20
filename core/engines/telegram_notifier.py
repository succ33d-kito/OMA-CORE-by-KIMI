"""O.M.A.-C.O.R.E. Telegram Notifier v2.1"""
import os
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

class TelegramNotifier:
    """Envia notificaciones de alertas CRITICAL a Telegram con formato detallado."""
    
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
            print("[Telegram] Notificaciones desactivadas")
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

    def send_critical_summary(self, opportunities: List[Dict[str, Any]], cycle_info: Dict[str, Any]) -> bool:
        if not self.enabled or not opportunities:
            return False
        if not self._can_send_critical():
            hours_since = (datetime.now(timezone.utc) - self._last_critical_alert).total_seconds() / 3600
            print(f"[Telegram] ⏳ Cooldown activo ({hours_since:.1f}h / {self._alert_cooldown_hours}h)")
            return False
        
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
        
        risk_emojis = {"VERY_HIGH": "🔴🔴 VERY_HIGH", "HIGH": "🔴 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW"}
        
        total = len(opportunities)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # Header del resumen
        lines = [
            f"<b>🚨 OMA-CORE RESUMEN CRITICAL</b>",
            f"<b>📅 {now} UTC</b>",
            f"",
            f"<b>📊 Total CRITICAL:</b> {total}",
            f"<b>🔄 Ciclo:</b> #{cycle_info.get('cycle', 'N/A')}",
            f"<b>⏱️ Proxima alerta:</b> En ~4 horas",
            f"",
            f"<b>═══════════════════════════════════════</b>",
            f"",
        ]
        
        # Cada oportunidad como "tarjeta" detallada
        for i, opp in enumerate(opportunities[:15], 1):
            opp_type = opp.get("opportunity_type", "UNKNOWN")
            emoji = type_emojis.get(opp_type, "📌")
            risk = opp.get("risk_level", "MEDIUM")
            risk_display = risk_emojis.get(risk, f"🟡 {risk}")
            assets = ", ".join(opp.get("assets", [])) or "N/A"
            score = opp.get("score", 0)
            conviction = opp.get("conviction", 0)
            action = opp.get("action_suggested", "N/A")
            timeframe = opp.get("action_details", {}).get("timeframe", "N/A")
            event_type = opp.get("event_type", "N/A")
            source = opp.get("source", "N/A")
            
            # Tarjeta de oportunidad
            lines.append(f"<b>━━━━━━━━━ #{i} ━━━━━━━━━</b>")
            lines.append(f"<b>{emoji} {opp_type}</b>")
            lines.append(f"")
            lines.append(f"<b>📋 Evento:</b> {event_type}")
            lines.append(f"<b>📈 Score:</b> {score}/100 | <b>🎯 Conviccion:</b> {conviction}/100")
            lines.append(f"<b>⚠️ Riesgo:</b> {risk_display}")
            lines.append(f"<b>💼 Assets:</b> {assets}")
            lines.append(f"")
            lines.append(f"<b>🎬 Accion:</b> {action}")
            lines.append(f"<b>⏱️ Timeframe:</b> {timeframe}")
            lines.append(f"<b>📡 Fuente:</b> {source}")
            lines.append(f"")
        
        if len(opportunities) > 15:
            lines.append(f"<b>... y {len(opportunities) - 15} mas en la DB</b>")
            lines.append(f"<i>Usa 'oma opportunities' para ver todas</i>")
        
        lines.append(f"<b>═══════════════════════════════════════</b>")
        
        message = "\n".join(lines)
        
        success = self.send_message(message)
        if success:
            self._mark_critical_sent()
        return success

    def test_connection(self) -> bool:
        if not self.enabled:
            print("[Telegram] ❌ Notificaciones desactivadas")
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
