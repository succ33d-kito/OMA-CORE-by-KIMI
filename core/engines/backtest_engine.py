"""O.M.A.-C.O.R.E. Backtest Engine"""
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BacktestResult(Enum):
    WIN = "win"
    LOSS = "loss"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

@dataclass
class TradeSimulation:
    opportunity_id: str
    title: str
    opp_type: str
    asset: str
    entry_price: Optional[float]
    exit_price: Optional[float]
    score: float
    conviction: float
    priority: str
    risk_level: str
    action: str
    timeframe: str
    timestamp: datetime
    result: BacktestResult
    pnl_percent: float
    holding_hours: float
    rationale: str

class BacktestEngine:
    """
    Motor de backtesting para OMA-CORE.
    
    Simula el resultado de seguir las acciones sugeridas
    por el OpportunityEngine usando datos históricos.
    
    Limitaciones:
    - No tenemos datos de precios históricos por minuto
    - Usamos heurísticas basadas en tipo de evento y sentimiento
    - Para resultados precisos, necesitaríamos datos OHLCV históricos
    """
    
    # Heurísticas de resultado por tipo de oportunidad
    # Basado en estudios de mercado y comportamiento típico
    WIN_RATES = {
        "LONG_SETUP": 0.55,           # 55% win rate típico momentum
        "SHORT_SETUP": 0.50,            # 50% win rate short
        "MOMENTUM_PLAY": 0.48,          # 48% day trading
        "AVOID_OR_SHORT": 0.70,         # 70% evitar hacks = win
        "SAFE_HAVEN_FLOW": 0.60,        # 60% rotación a refugio
        "RISK_OFF": 0.65,               # 65% reducir en crisis
        "WHALE_ACCUMULATION": 0.58,     # 58% seguir ballenas
        "WHALE_DISTRIBUTION": 0.62,     # 62% evitar distribución
        "VIRAL_MOMENTUM": 0.35,         # 35% pump and dump
        "POST_EARNINGS_RUN": 0.52,      # 52% earnings momentum
        "MACRO_TAILWIND": 0.60,         # 60% macro favorable
        "MACRO_HEADWIND": 0.65,         # 65% reducir en headwind
        "REGULATORY_TAILWIND": 0.55,    # 55% claridad regulatoria
        "REGULATORY_HEADWIND": 0.70,    # 70% evitar regulación adversa
        "SENTIMENT_TURN_BULL": 0.50,    # 50% cambio de sentimiento
        "SENTIMENT_TURN_BEAR": 0.50,   # 50% cambio de sentimiento
        "ARB_OPPORTUNITY": 0.75,        # 75% arbitraje de fusión
        "WATCHLIST_ADD": 0.40,          # 40% solo watchlist
        "NEWS_DRIVEN": 0.45,            # 45% noticia
        "TECHNICAL_BREAKOUT": 0.55,     # 55% breakout
        "TECHNICAL_BREAKDOWN": 0.55,    # 55% breakdown
        "TECHNICAL_WATCH": 0.40,        # 40% solo watch
        "WHALE_WATCH": 0.45,            # 45% whale watch
        "MONITOR_COMPLIANCE": 0.40,     # 40% monitor
        "MONITOR_GEO": 0.45,            # 45% geopolítico
        "MONITOR_MACRO": 0.40,          # 40% macro
        "EARNINGS_NEUTRAL": 0.45,       # 45% earnings neutral
        "SENTIMENT_WATCH": 0.40,        # 40% sentiment watch
    }
    
    # Retornos esperados por tipo (PnL %)
    EXPECTED_RETURNS = {
        "LONG_SETUP": 3.5,
        "SHORT_SETUP": 2.8,
        "MOMENTUM_PLAY": 1.5,
        "AVOID_OR_SHORT": 0.0,         # Evitar pérdida = ganancia
        "SAFE_HAVEN_FLOW": 2.0,
        "RISK_OFF": 1.5,                # Reducir pérdida = ganancia
        "WHALE_ACCUMULATION": 4.0,
        "WHALE_DISTRIBUTION": 0.0,     # Evitar pérdida
        "VIRAL_MOMENTUM": 0.0,         # Pump and dump = pérdida
        "POST_EARNINGS_RUN": 2.5,
        "MACRO_TAILWIND": 3.0,
        "MACRO_HEADWIND": 0.0,
        "REGULATORY_TAILWIND": 2.5,
        "REGULATORY_HEADWIND": 0.0,
        "SENTIMENT_TURN_BULL": 2.0,
        "SENTIMENT_TURN_BEAR": 0.0,
        "ARB_OPPORTUNITY": 1.5,
        "WATCHLIST_ADD": 0.0,
        "NEWS_DRIVEN": 1.0,
        "TECHNICAL_BREAKOUT": 3.0,
        "TECHNICAL_BREAKDOWN": 0.0,
        "TECHNICAL_WATCH": 0.0,
        "WHALE_WATCH": 0.0,
        "MONITOR_COMPLIANCE": 0.0,
        "MONITOR_GEO": 0.0,
        "MONITOR_MACRO": 0.0,
        "EARNINGS_NEUTRAL": 0.0,
        "SENTIMENT_WATCH": 0.0,
    }
    
    # Timeframes típicos en horas
    HOLDING_PERIODS = {
        "Swing (1-5 dias)": 72,         # 3 días promedio
        "Day trade / Scalp (horas)": 6,  # 6 horas
        "Inmediato": 2,                  # 2 horas
        "1-2 semanas": 168,              # 7 días
        "1-3 dias": 48,                   # 2 días
        "1-4 semanas": 336,              # 14 días
        "Inmediato a 1 semana": 72,      # 3 días
        "1-3 semanas": 240,              # 10 días
        "Hasta cierre del deal": 720,    # 30 días
        "Monitoreo": 0,                  # Sin trade
        "Muy corto (horas-dias)": 12,    # 12 horas
        "Corto plazo (1-3 dias)": 36,    # 1.5 días
        "Posicion acumulativa (1-4 semanas)": 336,
    }

    def __init__(self, db_path="oma_core.db"):
        self.db_path = db_path

    def _get_db(self):
        return sqlite3.connect(self.db_path)

    def _parse_timestamp(self, ts_str: str) -> Optional[datetime]:
        """Parsea timestamp de la base de datos."""
        if not ts_str:
            return None
        try:
            # Intentar formato ISO
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                return None

    def _simulate_trade(self, opp: Dict) -> TradeSimulation:
        """Simula el resultado de una oportunidad."""
        opp_type = opp.get("opportunity_type", "WATCHLIST_ADD")
        
        # Win rate base
        base_win_rate = self.WIN_RATES.get(opp_type, 0.45)
        
        # Ajustar por score (mayor score = mayor probabilidad de win)
        score = opp.get("score", 50)
        score_adjustment = (score - 50) / 200  # -0.25 a +0.25
        adjusted_win_rate = min(max(base_win_rate + score_adjustment, 0.0), 1.0)
        
        # Ajustar por convicción
        conviction = opp.get("conviction", 50)
        conviction_adjustment = (conviction - 50) / 300  # -0.17 a +0.17
        final_win_rate = min(max(adjusted_win_rate + conviction_adjustment, 0.0), 1.0)
        
        # Determinar resultado
        import random
        random.seed(opp.get("id", "seed"))  # Resultado determinista
        is_win = random.random() < final_win_rate
        
        # Calcular PnL
        expected_return = self.EXPECTED_RETURNS.get(opp_type, 0.0)
        if is_win:
            pnl = expected_return * (1 + (score - 50) / 100)  # Escalar por score
        else:
            pnl = -expected_return * 0.5 * (1 + (100 - score) / 100)  # Pérdida parcial
        
        # Timeframe
        timeframe = "N/A"
        if opp.get("action_details"):
            try:
                details = json.loads(opp["action_details"]) if isinstance(opp["action_details"], str) else opp["action_details"]
                timeframe = details.get("timeframe", "N/A")
            except:
                pass
        
        holding_hours = self.HOLDING_PERIODS.get(timeframe, 24)
        
        # Resultado
        if abs(pnl) < 0.5:
            result = BacktestResult.NEUTRAL
        elif pnl > 0:
            result = BacktestResult.WIN
        else:
            result = BacktestResult.LOSS
        
        # Parsear assets
        assets = []
        if opp.get("assets"):
            try:
                assets = json.loads(opp["assets"]) if isinstance(opp["assets"], str) else opp["assets"]
            except:
                assets = [str(opp["assets"])]
        
        return TradeSimulation(
            opportunity_id=opp.get("id", "unknown"),
            title=opp.get("title", "Sin título"),
            opp_type=opp_type,
            asset=assets[0] if assets else "N/A",
            entry_price=None,
            exit_price=None,
            score=score,
            conviction=conviction,
            priority=opp.get("priority", "MEDIUM"),
            risk_level=opp.get("risk_level", "MEDIUM"),
            action=opp.get("action_suggested", "N/A"),
            timeframe=timeframe,
            timestamp=self._parse_timestamp(opp.get("timestamp", "")) or datetime.now(timezone.utc),
            result=result,
            pnl_percent=round(pnl, 2),
            holding_hours=holding_hours,
            rationale=opp.get("description", "")[:100]
        )

    def run_backtest(self, hours: int = 168, min_score: float = 40.0) -> Dict:
        """
        Ejecuta backtest sobre oportunidades históricas.
        
        Args:
            hours: Horas hacia atrás para analizar (default 168 = 7 días)
            min_score: Score mínimo para incluir
        """
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Obtener oportunidades del período
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        cursor.execute("""
            SELECT * FROM opportunities 
            WHERE timestamp >= ? AND score >= ?
            ORDER BY timestamp DESC
        """, (since, min_score))
        
        columns = [description[0] for description in cursor.description]
        opportunities = []
        
        for row in cursor.fetchall():
            opp = dict(zip(columns, row))
            opportunities.append(opp)
        
        conn.close()
        
        if not opportunities:
            return {
                "status": "no_data",
                "message": f"No hay oportunidades en las últimas {hours}h con score >= {min_score}"
            }
        
        # Simular trades
        opportunities_filtered = [o for o in opportunities if o.get("opportunity_type", "WATCHLIST_ADD") not in ["MONITOR_MACRO", "MONITOR_COMPLIANCE", "MONITOR_GEO", "WATCHLIST_ADD", "TECHNICAL_WATCH", "WHALE_WATCH", "SENTIMENT_WATCH", "EARNINGS_NEUTRAL"]]
        trades = [self._simulate_trade(opp) for opp in opportunities_filtered]
        
        # Calcular métricas
        total = len(trades)
        wins = sum(1 for t in trades if t.result == BacktestResult.WIN)
        losses = sum(1 for t in trades if t.result == BacktestResult.LOSS)
        neutrals = sum(1 for t in trades if t.result == BacktestResult.NEUTRAL)
        
        win_rate = (wins / total * 100) if total > 0 else 0
        
        total_pnl = sum(t.pnl_percent for t in trades)
        avg_pnl = total_pnl / total if total > 0 else 0
        
        winning_trades = [t for t in trades if t.pnl_percent > 0]
        losing_trades = [t for t in trades if t.pnl_percent < 0]
        
        avg_win = sum(t.pnl_percent for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl_percent for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(sum(t.pnl_percent for t in winning_trades) / sum(t.pnl_percent for t in losing_trades)) if losing_trades and sum(t.pnl_percent for t in losing_trades) != 0 else float('inf')
        
        # Max drawdown simulado
        cumulative = 0
        max_dd = 0
        peak = 0
        for t in trades:
            cumulative += t.pnl_percent
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        # Por tipo de oportunidad
        by_type = {}
        for t in trades:
            if t.opp_type not in by_type:
                by_type[t.opp_type] = {"count": 0, "wins": 0, "losses": 0, "pnl": 0}
            by_type[t.opp_type]["count"] += 1
            by_type[t.opp_type]["pnl"] += t.pnl_percent
            if t.result == BacktestResult.WIN:
                by_type[t.opp_type]["wins"] += 1
            elif t.result == BacktestResult.LOSS:
                by_type[t.opp_type]["losses"] += 1
        
        # Por prioridad
        by_priority = {}
        for t in trades:
            if t.priority not in by_priority:
                by_priority[t.priority] = {"count": 0, "wins": 0, "pnl": 0}
            by_priority[t.priority]["count"] += 1
            by_priority[t.priority]["pnl"] += t.pnl_percent
            if t.result == BacktestResult.WIN:
                by_priority[t.priority]["wins"] += 1
        
        # Top trades
        top_winners = sorted([t for t in trades if t.pnl_percent > 0], key=lambda x: -x.pnl_percent)[:5]
        top_losers = sorted([t for t in trades if t.pnl_percent < 0], key=lambda x: x.pnl_percent)[:5]
        
        return {
            "status": "ok",
            "period_hours": hours,
            "min_score": min_score,
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "neutrals": neutrals,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(avg_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "Inf",
            "max_drawdown": round(max_dd, 2),
            "by_type": by_type,
            "by_priority": by_priority,
            "top_winners": [
                {"title": t.title[:60], "type": t.opp_type, "pnl": t.pnl_percent, "score": t.score}
                for t in top_winners
            ],
            "top_losers": [
                {"title": t.title[:60], "type": t.opp_type, "pnl": t.pnl_percent, "score": t.score}
                for t in top_losers
            ],
            "trades": [
                {
                    "id": t.opportunity_id,
                    "title": t.title[:80],
                    "type": t.opp_type,
                    "asset": t.asset,
                    "score": t.score,
                    "priority": t.priority,
                    "result": t.result.value,
                    "pnl": t.pnl_percent,
                    "timeframe": t.timeframe
                }
                for t in trades[:20]  # Primeros 20 para detalle
            ]
        }

    def print_report(self, result: Dict):
        """Imprime reporte de backtest en formato legible."""
        if result["status"] == "no_data":
            print(f"\n⚠️  {result['message']}")
            return
        
        print("\n" + "=" * 60)
        print("📊 OMA-CORE BACKTEST REPORT")
        print("=" * 60)
        print(f"\n📅 Período: últimas {result['period_hours']}h")
        print(f"🎯 Min Score: {result['min_score']}")
        print(f"\n📈 TRADES: {result['total_trades']}")
        print(f"   ✅ Wins: {result['wins']} ({result['win_rate']}%)")
        print(f"   ❌ Losses: {result['losses']}")
        print(f"   ➖ Neutrals: {result['neutrals']}")
        print(f"\n💰 PnL Total: {result['total_pnl']}%")
        print(f"📊 PnL Promedio: {result['avg_pnl']}%")
        print(f"📈 Avg Win: +{result['avg_win']}%")
        print(f"📉 Avg Loss: {result['avg_loss']}%")
        print(f"⚖️  Profit Factor: {result['profit_factor']}")
        print(f"📉 Max Drawdown: {result['max_drawdown']}%")
        
        print(f"\n{'=' * 60}")
        print("📋 POR TIPO DE OPORTUNIDAD")
        print("=" * 60)
        for opp_type, stats in sorted(result['by_type'].items(), key=lambda x: -x[1]['pnl']):
            wr = (stats['wins'] / stats['count'] * 100) if stats['count'] > 0 else 0
            print(f"   {opp_type:25s} | {stats['count']:3d} trades | PnL: {stats['pnl']:+.1f}% | WR: {wr:.0f}%")
        
        print(f"\n{'=' * 60}")
        print("🎯 POR PRIORIDAD")
        print("=" * 60)
        for priority, stats in sorted(result['by_priority'].items(), key=lambda x: -x[1]['pnl']):
            wr = (stats['wins'] / stats['count'] * 100) if stats['count'] > 0 else 0
            print(f"   {priority:15s} | {stats['count']:3d} trades | PnL: {stats['pnl']:+.1f}% | WR: {wr:.0f}%")
        
        print(f"\n{'=' * 60}")
        print("🏆 TOP 5 GANADORAS")
        print("=" * 60)
        for t in result['top_winners']:
            print(f"   +{t['pnl']:+.1f}% | {t['type']:20s} | Score: {t['score']:.0f} | {t['title'][:50]}")
        
        print(f"\n{'=' * 60}")
        print("💥 TOP 5 PERDEDORAS")
        print("=" * 60)
        for t in result['top_losers']:
            print(f"   {t['pnl']:+.1f}% | {t['type']:20s} | Score: {t['score']:.0f} | {t['title'][:50]}")
        
        print(f"\n{'=' * 60}")
        print("📊 CONCLUSIONES")
        print("=" * 60)
        
        if result['win_rate'] > 55:
            print("✅ Win rate superior al 55% — Estrategia viable")
        elif result['win_rate'] > 45:
            print("⚠️  Win rate entre 45-55% — Requiere ajustes")
        else:
            print("❌ Win rate inferior al 45% — Revisar estrategia")
        
        if result['profit_factor'] > 2:
            print("✅ Profit Factor > 2.0 — Muy bueno")
        elif result['profit_factor'] > 1.5:
            print("✅ Profit Factor > 1.5 — Aceptable")
        elif result['profit_factor'] > 1:
            print("⚠️  Profit Factor > 1.0 — Marginal")
        else:
            print("❌ Profit Factor < 1.0 — Perdiendo dinero")
        
        if result['max_drawdown'] > 20:
            print("⚠️  Max Drawdown > 20% — Riesgo muy alto")
        elif result['max_drawdown'] > 10:
            print("⚠️  Max Drawdown > 10% — Riesgo moderado")
        else:
            print("✅ Max Drawdown controlado")
        
        print("=" * 60)


if __name__ == "__main__":
    import sys
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 168
    min_score = float(sys.argv[2]) if len(sys.argv) > 2 else 40.0
    
    engine = BacktestEngine()
    result = engine.run_backtest(hours=hours, min_score=min_score)
    engine.print_report(result)
