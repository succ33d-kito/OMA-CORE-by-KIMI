"""Slippage Reality Test — Phase 1-3: measure alpha survival under costs

Usage: python scripts/slippage_test.py
"""
import sys; sys.path.insert(0, ".")
from statistics import mean, stdev
from math import sqrt
from collections import defaultdict
from datetime import datetime

from core.schemas.event_schema import Event, EventType, Asset, AssetClass, Urgency
from core.schemas.trade_schema import TradeDirection
from core.agents.market_agent import MarketAgent
from core.agents.risk_agent import RiskAgent
from core.council.council import AgentCouncil
from core.execution.paper_trading import PaperTradingEngine
from core.execution.performance_memory import PerformanceMemory
from core.execution.slippage import SlippageEngine

SYMBOLS = ["BTC", "ETH", "SOL"]
BNB_MAP = {"BTC":"BTCUSDT","ETH":"ETHUSDT","SOL":"SOLUSDT"}

def fetch_ohlcv(symbol, days):
    import requests as req
    pair = BNB_MAP.get(symbol)
    if not pair:
        return None
    try:
        resp = req.get("https://api.binance.com/api/v3/klines",
            params={"symbol": pair, "interval": "1h", "limit": min(days * 24, 1000)}, timeout=15)
        if resp.status_code == 200:
            return [
                {"time": datetime.fromtimestamp(k[0]/1000), "open": float(k[1]),
                 "high": float(k[2]), "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])}
                for k in resp.json()
            ]
    except: pass
    try:
        import yfinance as yf
        hist = yf.Ticker(symbol).history(period=f"{days}d", interval="1h")
        if not hist.empty:
            return [{"time": idx.to_pydatetime(), "open": float(r["Open"]), "high": float(r["High"]),
                     "low": float(r["Low"]), "close": float(r["Close"]), "volume": float(r["Volume"])}
                    for idx, r in hist.iterrows()]
    except: pass
    return None

def generate_events(symbol, ohlcv):
    events = []
    for i in range(1, len(ohlcv)):
        p, c = ohlcv[i-1], ohlcv[i]
        ch = (c["close"] - p["close"]) / p["close"]
        u = Urgency.HIGH if abs(ch) > 0.05 else Urgency.MEDIUM if abs(ch) > 0.02 else Urgency.LOW
        events.append(Event(
            id=f"{symbol}_{i}", source="slippage_test",
            event_type=EventType.PRICE_MOVEMENT,
            title=f"{symbol} {ch*100:+.2f}%",
            assets=[Asset(symbol=symbol, name=symbol, asset_class=AssetClass.CRYPTO, price_at_event=c["close"])],
            timestamp=c["time"], detected_at=c["time"],
            urgency=u, sentiment_score=ch, confidence=0.7,
        ))
    return events

def run_with_slippage(days, slippage_pct, spread_mode="none"):
    spread_bps = {"BTC": 1.0, "ETH": 2.0, "SOL": 3.0} if spread_mode == "real" else {}
    sl = SlippageEngine(slippage_pct=slippage_pct, spread_bps=spread_bps)

    ohlcv = {}
    for sym in SYMBOLS:
        d = fetch_ohlcv(sym, days + 5)
        if d and len(d) >= 50:
            ohlcv[sym] = d

    market = MarketAgent()
    market._fetch_ohlcv = lambda s: ohlcv.get(s)
    risk = RiskAgent()
    risk._fetch_ohlcv = lambda s: ohlcv.get(s)
    council = AgentCouncil()
    perf = PerformanceMemory()
    engine = PaperTradingEngine(initial_capital=10000.0, performance_memory=perf, council=council,
                                slippage_engine=sl)

    all_events = []
    for sym, data in ohlcv.items():
        all_events.extend(generate_events(sym, data))
    all_events.sort(key=lambda e: e.timestamp)

    # ATR×3.0 override
    orig_process = engine.process_decision
    def process_atr(decision):
        signal = orig_process(decision)
        if signal and decision.opinions:
            meta = decision.opinions[0].metadata
            if "atr_14" in meta and meta.get("price", 0) > 0:
                atr_pct = meta["atr_14"] / meta["price"] * 100
                stop_pct = max(atr_pct * 3.0, 1.0)
                price = meta["price"]
                target_pct = stop_pct * 2
                if signal.direction == TradeDirection.LONG:
                    sl_r = price * (1 - stop_pct / 100)
                    tp_r = price * (1 + target_pct / 100)
                else:
                    sl_r = price * (1 + stop_pct / 100)
                    tp_r = price * (1 - target_pct / 100)
                signal.stop_loss = sl.stop_price(sl_r, signal.direction.value, signal.asset)
                signal.take_profit = sl.target_price(tp_r, signal.direction.value, signal.asset)
        return signal
    engine.process_decision = process_atr

    price_hist = {s: [] for s in SYMBOLS}
    for event in all_events:
        sym = event.assets[0].symbol
        p = event.assets[0].price_at_event
        price_hist[sym].append((event.timestamp, p))

        opinions = []
        for agent in [market, risk]:
            op = agent.analyze(event)
            if op: opinions.append(op)
        if len(opinions) < 2: continue
        for op in opinions: council.submit_opinion(op)
        decision = council.decide(event.id)
        signal = engine.process_decision(decision)
        if signal: engine.execute_signal(signal)
        cur = {s: (price_hist[s][-1][1] if price_hist[s] else 0) for s in SYMBOLS}
        engine.check_positions(cur)

    final = {s: (price_hist[s][-1][1] if price_hist[s] else 0) for s in SYMBOLS}
    engine.check_positions(final)

    # Compute metrics
    t = engine.closed_trades
    pnls = [x.pnl_percent or 0 for x in t]
    abs_pnls = [x.pnl_absolute or 0 for x in t]
    n = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    wr = wins / n * 100 if n else 0
    total_pnl = sum(pnls)
    avg_pnl = mean(pnls) if pnls else 0
    sd = stdev(pnls) if len(pnls) > 1 else 0.001
    sharpe = (mean(pnls) / sd) * sqrt(365) if sd > 0 else 0
    win_pnls = [p for p in pnls if p > 0]
    loss_pnls = [p for p in pnls if p < 0]
    pf = abs(sum(win_pnls) / sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else float("inf")

    equity = 10000.0
    peak = 10000.0
    max_dd = 0.0
    for ap in abs_pnls:
        equity += ap
        if equity > peak: peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd: max_dd = dd

    final_equity = 10000.0 + sum(abs_pnls)
    total_ret = (final_equity - 10000) / 10000 * 100

    by_dir = defaultdict(list)
    for x in engine.closed_trades:
        by_dir[x.signal.direction.value].append(x.pnl_percent or 0)

    return {
        "n": n, "wr": wr, "return": total_ret, "sharpe": sharpe,
        "pf": pf, "max_dd": max_dd, "avg_pnl": avg_pnl,
        "equity": final_equity,
        "long_wr": (sum(1 for p in by_dir.get("long", []) if p > 0) / len(by_dir["long"]) * 100) if by_dir.get("long") else 0,
        "short_wr": (sum(1 for p in by_dir.get("short", []) if p > 0) / len(by_dir["short"]) * 100) if by_dir.get("short") else 0,
        "long_n": len(by_dir.get("long", [])),
        "short_n": len(by_dir.get("short", [])),
    }

if __name__ == "__main__":
    print("=" * 70)
    print("  ALPHA SURVIVAL TEST — Slippage & Spread Impact")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    days = 30
    configs = [
        ("No costs", 0.0, "none"),
        ("0.05% slippage", 0.05, "none"),
        ("0.10% slippage", 0.10, "none"),
        ("0.25% slippage", 0.25, "none"),
        ("0.50% slippage", 0.50, "none"),
        ("0.10% + real spread", 0.10, "real"),
        ("0.25% + real spread", 0.25, "real"),
    ]

    print(f"\n  Days: {days} | Config: MarketAgent + RiskAgent + Council | ATR×3.0 | Both directions")
    print(f"\n  {'Cost Model':>25s} | {'Trades':>6s} | {'WR':>6s} | {'Return':>9s} | {'Sharpe':>7s} | {'PF':>7s} | {'MaxDD':>7s} | {'LONG':>6s} | {'SHORT':>6s}")
    print(f"  {'-'*25} | {'-'*6} | {'-'*6} | {'-'*9} | {'-'*7} | {'-'*7} | {'-'*7} | {'-'*6} | {'-'*6}")

    results = []
    for label, slip, spread in configs:
        r = run_with_slippage(days, slip, spread)
        results.append((label, r))
        print(f"  {label:>25s} | {r['n']:>6d} | {r['wr']:>5.1f}% | {r['return']:>+8.2f}% | {r['sharpe']:>7.2f} | {r['pf']:>7.2f} | {r['max_dd']:>6.2f}% | {r['long_n']:>3d}/{r['long_wr']:>5.1f}% | {r['short_n']:>3d}/{r['short_wr']:>5.1f}%")

    # Survival analysis
    baseline = results[0][1]
    print(f"\n  --- Alpha Survival Analysis ---")
    print(f"  {'Cost Model':>25s} | {'Return Δ':>10s} | {'Sharpe Δ':>9s} | {'PF Δ':>9s} | {'Survival':>9s}")
    print(f"  {'-'*25} | {'-'*10} | {'-'*9} | {'-'*9} | {'-'*9}")
    for label, r in results:
        ret_delta = r['return'] - baseline['return']
        sharpe_delta = r['sharpe'] - baseline['sharpe']
        pf_ratio = r['pf'] / baseline['pf'] * 100 if baseline['pf'] else 0
        survival = r['return'] / baseline['return'] * 100 if baseline['return'] else 0
        print(f"  {label:>25s} | {ret_delta:>+9.2f}% | {sharpe_delta:>+8.2f} | {pf_ratio:>7.1f}% | {survival:>7.1f}%")
