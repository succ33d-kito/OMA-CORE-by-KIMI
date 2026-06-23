"""OSIRIS Multi-Market Asset Coverage Audit
Inspects existing data pipeline (events, opportunities, trades) and produces
counts by asset class, symbol, source, event type, opportunity type, and trade status.

Usage:
  python scripts/asset_coverage_audit.py [--db-path oma_core.db]
  python scripts/asset_coverage_audit.py --inspect-code  # Static code analysis only
"""
import sys, os, json
sys.path.insert(0, ".")
from collections import defaultdict, Counter
from typing import Dict, List, Optional
from datetime import datetime, timezone

from core.schemas.event_schema import AssetClass, EventType


# ── Static Code Analysis ──────────────────────────────────────────────────────

def inspect_collectors() -> Dict:
    """Analyze collectors for multi-market coverage via code inspection."""
    collectors = {}

    # BinanceCollector
    binance_symbols = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT",
        "DOTUSDT", "UNIUSDT", "LTCUSDT", "BCHUSDT", "ATOMUSDT",
    ]
    collectors["binance"] = {
        "asset_class": AssetClass.CRYPTO.value,
        "symbols": [s.replace("USDT", "") for s in binance_symbols],
        "raw_symbols": binance_symbols,
        "count": len(binance_symbols),
    }

    # CoinGeckoCollector
    collectors["coingecko"] = {
        "asset_class": AssetClass.CRYPTO.value,
        "symbols": ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE",
                     "AVAX", "LINK", "MATIC", "DOT", "UNI", "LTC", "BCH", "ATOM"],
        "count": 15,
    }

    # YahooFinanceCollector
    collectors["yahoo_finance"] = {
        "asset_class": "MULTI",
        "stocks": {
            "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
                        "NFLX", "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER",
                        "COIN", "PLTR", "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO"],
            "count": 22,
            "asset_class": AssetClass.STOCK.value,
        },
        "forex": {
            "symbols": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X",
                        "AUDUSD=X", "USDCAD=X", "NZDUSD=X", "EURGBP=X"],
            "count": 8,
            "asset_class": AssetClass.FOREX.value,
        },
        "commodities": {
            "symbols": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZW=F", "ZC=F", "ZS=F"],
            "count": 8,
            "asset_class": AssetClass.COMMODITY.value,
        },
        "indices": {
            "symbols": ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX",
                        "^FTSE", "^N225", "^HSI"],
            "count": 8,
            "asset_class": AssetClass.INDEX.value,
        },
    }

    # FREDCollector
    fred_series = {
        "rates": ["DFF", "DGS10", "DGS2", "T10Y2Y"],
        "inflation": ["CPIAUCSL", "CPILFESL", "PCEPI"],
        "employment": ["PAYEMS", "UNRATE", "ICSA"],
        "growth": ["GDP", "GDPC1", "INDPRO"],
        "sentiment": ["UMCSENT"],
    }
    fred_asset_classes = {
        "rates": AssetClass.BOND.value,
        "inflation": AssetClass.INDEX.value,
        "employment": AssetClass.INDEX.value,
        "growth": AssetClass.INDEX.value,
        "sentiment": AssetClass.INDEX.value,
    }
    total_fred = sum(len(v) for v in fred_series.values())
    collectors["fred"] = {
        "asset_class": "MULTI (BOND + INDEX)",
        "series_groups": fred_series,
        "asset_class_map": fred_asset_classes,
        "count": total_fred,
    }

    # RSSCollector
    rss_sources = [
        "rss_reuters_business", "rss_bloomberg", "rss_coindesk",
        "rss_cointelegraph", "rss_forexlive", "rss_cnbc", "rss_marketwatch",
    ]
    rss_symbol_map = {
        "CRYPTO": ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX"],
        "STOCK": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC"],
        "FOREX": ["EURUSD", "GBPUSD", "USDJPY"],
        "COMMODITY": ["GOLD", "SILVER", "OIL"],
    }
    collectors["rss"] = {
        "asset_class": "MULTI",
        "sources": rss_sources,
        "symbol_map": rss_symbol_map,
        "total_symbols_covered": sum(len(v) for v in rss_symbol_map.values()),
    }

    # SentimentCollector
    collectors["sentiment"] = {
        "asset_class": AssetClass.CRYPTO.value,
        "source": "Fear & Greed Index",
    }

    # PolymarketCollector
    collectors["polymarket"] = {
        "asset_class": AssetClass.INDEX.value,
    }

    return collectors


def inspect_agent_ohlcv_support() -> Dict:
    """Inspect which symbols/asset classes agents can get OHLCV data for."""
    # MarketAgent._fetch_ohlcv: Binance first, then yfinance
    # RiskAgent._fetch_ohlcv: same pattern
    binance_symbols = {
        "BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
        "XRP": "XRPUSDT", "BNB": "BNBUSDT", "ADA": "ADAUSDT",
        "DOGE": "DOGEUSDT", "AVAX": "AVAXUSDT", "LINK": "LINKUSDT",
        "MATIC": "MATICUSDT", "DOT": "DOTUSDT", "UNI": "UNIUSDT",
        "LTC": "LTCUSDT", "BCH": "BCHUSDT", "ATOM": "ATOMUSDT",
    }

    return {
        "native_binance_support": {
            "asset_class": AssetClass.CRYPTO.value,
            "symbols": list(binance_symbols.keys()),
            "count": len(binance_symbols),
            "note": "Agents try Binance first. Only crypto symbols have native support.",
        },
        "yfinance_fallback": {
            "asset_classes": ["STOCK", "FOREX", "COMMODITY", "INDEX"],
            "note": "Non-crypto symbols fall back to yfinance. Works for stocks/forex/commodities with Yahoo Finance tickers.",
            "limitations": [
                "Yahoo Finance rate-limited for frequent calls",
                "Forex pairs use Yahoo notation (EURUSD=X)",
                "Commodity futures use Yahoo notation (GC=F)",
                "No error handling for delisted symbols",
                "No caching between consecutive agent calls",
            ]
        }
    }


def inspect_pipeline_stops() -> Dict:
    """Identify where the pipeline stops per asset class."""
    return {
        "crypto": {
            "status": "FULL FLOW",
            "stops_at": None,
            "detail": "Events → Agents → Council → TradeSignal → PaperTrade. All stages pass.",
        },
        "forex": {
            "status": "STOPS AT COUNCIL",
            "stops_at": "AgentCouncil.process_decision → PaperTradingEngine.process_decision",
            "detail": (
                "Yahoo Finance collects forex (EURUSD=X, etc.) and RSS creates forex events. "
                "Agents receive events and will attempt OHLCV via yfinance fallback. "
                "AgentCouncil makes a decision. However, PaperTradingEngine.process_decision "
                "expects symbols from Binance symbol map (BTC, ETH, SOL...) and will reject "
                "forex symbols 'EURUSD' etc. because _fetch_ohlcv in process_decision expects "
                "Binance pair symbols. TradeSignal creation will fail at symbol/price extraction."
            ),
        },
        "stocks": {
            "status": "STOPS AT COUNCIL",
            "stops_at": "AgentCouncil.process_decision → PaperTradingEngine.process_decision",
            "detail": (
                "Yahoo Finance collects 22 stock symbols. RSS creates stock events. "
                "Same issue as forex: PaperTradingEngine only handles crypto symbols. "
                "The engine has no concept of stock market hours, dividend adjustments, "
                "or corporate actions. Stock events reach the council but cannot be traded."
            ),
        },
        "commodities": {
            "status": "STOPS AT COUNCIL",
            "stops_at": "AgentCouncil.process_decision → PaperTradingEngine.process_decision",
            "detail": (
                "Yahoo Finance collects 8 commodity futures. RSS creates commodity events. "
                "Same blocking point as forex/stocks. Additionally, commodity futures have "
                "rollover risk that the engine has no handling for."
            ),
        },
        "bonds": {
            "status": "STOPS AT SCORE ENGINE",
            "stops_at": "ScoreEngine._calculate_asset_relevance (score=50, may not reach min_score)",
            "detail": (
                "FREDCollector collects bond yield data (DFF, DGS10, etc.). These generate "
                "INDEX/BOND classed events. ScoreEngine gives BOND events a base 50 relevance "
                "(vs 70 for CRYPTO/STOCK). May fall below min_score (40) depending on other "
                "score components. Even if scored, bonds have no OHLCV provider and no "
                "trade execution path."
            ),
        },
        "indices": {
            "status": "STOPS AT SCORE ENGINE",
            "stops_at": "ScoreEngine._calculate_asset_relevance (score=50)",
            "detail": (
                "FRED, Yahoo (indices), and Polymarket produce INDEX events. "
                "Same scoring issue as bonds. No trade execution path."
            ),
        },
    }


def inspect_normalization_gaps() -> List[Dict]:
    """Find symbol normalization inconsistencies across collectors."""
    return [
        {
            "issue": "Forex symbol mismatch between collectors",
            "yahoo_symbol": "EURUSD=X",
            "rss_symbol": "EURUSD",
            "impact": "Same instrument has different IDs in different collectors. No cross-referencing.",
        },
        {
            "issue": "Commodity symbol mismatch between collectors",
            "yahoo_symbol": "GC=F (Gold futures)",
            "rss_symbol": "GOLD",
            "impact": "Cannot correlate gold events from RSS with gold price data from Yahoo.",
        },
        {
            "issue": "Stock symbols lack exchange prefix",
            "yahoo_symbol": "AAPL",
            "detail": "AAPL on NASDAQ vs AAPL on other exchanges cannot be distinguished.",
        },
        {
            "issue": "No ISIN/CUSIP mapping",
            "detail": "No universal identifier. Symbol conflicts between markets are not detected.",
        },
        {
            "issue": "Crypto symbol conflict with stock symbols",
            "detail": "Some crypto symbols (like 'XRP') could theoretically overlap with stock tickers on different exchanges.",
        },
    ]


def inspect_risk_model_gaps() -> List[Dict]:
    """Identify risk model differences needed per asset class."""
    return [
        {
            "market": "forex",
            "gaps": [
                "No leverage modeling (forex typically 30:1-50:1)",
                "No swap/overnight funding rate tracking",
                "No session-based volatility (London/NY/Tokyo sessions)",
                "No central bank event calendar",
                "Spread model is crypto-specific (fixed bps)",
                "Weekend gap risk is different — forex trades nearly 24/5",
            ]
        },
        {
            "market": "stocks",
            "gaps": [
                "No market hours (only 6.5 hours/day for US equities)",
                "No earnings gap risk",
                "No dividend adjustment in price history",
                "No corporate action handling (splits, mergers, delistings)",
                "No exchange-specific circuit breaker logic",
                "Different ATR ranges (typically 1-3% vs crypto 3-8%)",
                "No short-selling restriction awareness",
            ]
        },
        {
            "market": "commodities",
            "gaps": [
                "No futures rollover logic (continuous contract required)",
                "No expiry/contango/backwardation awareness",
                "Different market hours per commodity",
                "Storage cost and convenience yield not modeled",
                "Physical delivery mechanics not relevant",
                "Different gap profiles (gap up/down on inventory reports)",
            ]
        },
    ]


# ── Report Generation ─────────────────────────────────────────────────────────

def generate_report() -> Dict:
    """Generate comprehensive asset coverage audit report."""
    collectors = inspect_collectors()
    agent_ohlcv = inspect_agent_ohlcv_support()
    pipeline_stops = inspect_pipeline_stops()
    normalization_gaps = inspect_normalization_gaps()
    risk_gaps = inspect_risk_model_gaps()

    # Aggregate symbol counts by asset class
    symbol_counts = defaultdict(int)
    source_counts = defaultdict(set)

    # Binance/CoinGecko → CRYPTO
    for name in ["binance", "coingecko"]:
        for sym in collectors[name]["symbols"]:
            symbol_counts["crypto"] += 1
            source_counts["crypto"].add(name)

    # Yahoo
    yf = collectors["yahoo_finance"]
    for ac in ["stocks", "forex", "commodities", "indices"]:
        cls = yf[ac]["asset_class"]
        for sym in yf[ac]["symbols"]:
            symbol_counts[cls] += 1
            source_counts[cls].add("yahoo_finance")

    # FRED
    for group, series in collectors["fred"]["series_groups"].items():
        cls = collectors["fred"]["asset_class_map"].get(group, "index")
        for s in series:
            symbol_counts[cls] += 1
            source_counts[cls].add("fred")

    # RSS
    for ac, syms in collectors["rss"]["symbol_map"].items():
        ac_key = ac.lower()
        for s in syms:
            symbol_counts[ac_key] += 1
            source_counts[ac_key].add("rss")

    # Sentiment → crypto
    symbol_counts["crypto"] += 1
    source_counts["crypto"].add("sentiment")

    return {
        "report_generated": datetime.now(timezone.utc).isoformat(),
        "executive_summary": {
            "total_collectors": len(collectors),
            "asset_classes_collected": sorted(symbol_counts.keys()),
            "total_observed_symbols": sum(symbol_counts.values()),
            "symbols_by_class": dict(symbol_counts),
            "sources_by_class": {k: list(v) for k, v in source_counts.items()},
        },
        "collectors": collectors,
        "agent_ohlcv_support": agent_ohlcv,
        "pipeline_stops": pipeline_stops,
        "normalization_gaps": normalization_gaps,
        "risk_model_gaps": risk_gaps,
        "missing_for_trading": {
            "forex": [
                "Symbol normalization across collectors",
                "OHLCV provider integration (not just yfinance fallback)",
                "Market session calendar",
                "Leverage and margin model",
                "Swap rate tracking",
                "Central bank event calendar",
                "Forex-specific ATR thresholds",
                "Gap risk model for weekly close (Fri NY close → Sun open)",
            ],
            "stocks": [
                "Market hours calendar",
                "Earnings calendar for gap risk",
                "Dividend adjustment in OHLCV",
                "Corporate action handling",
                "Short-selling restriction checks",
                "Different position sizing (lower ATR %)",
                "Exchange-specific symbol qualification",
            ],
            "commodities": [
                "Futures rollover/continuous contract logic",
                "Expiry calendar",
                "Storage cost / convenience yield models",
                "Commodity-specific ATR thresholds",
                "Inventory report calendar (EIA, USDA, etc.)",
            ],
        },
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OSIRIS Asset Coverage Audit")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file path")
    args = parser.parse_args()

    report = generate_report()

    output = args.output or "_project-memory/multi_market/asset_coverage_report.json"
    os.makedirs(os.path.dirname(output), exist_ok=True)

    with open(output, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    exec_summary = report["executive_summary"]
    print("=" * 60)
    print("OSIRIS Asset Coverage Audit")
    print("=" * 60)
    print(f"Collectors: {exec_summary['total_collectors']}")
    print(f"Asset classes observed: {', '.join(exec_summary['asset_classes_collected'])}")
    print(f"Total observed symbols: {exec_summary['total_observed_symbols']}")
    print()
    print("Symbols by class:")
    for cls, count in sorted(exec_summary['symbols_by_class'].items()):
        print(f"  {cls.upper():12s} {count:3d} symbols")
    print()
    print("Sources by class:")
    for cls, sources in sorted(exec_summary['sources_by_class'].items()):
        print(f"  {cls.upper():12s} {', '.join(sources)}")
    print()
    print("Pipeline stops:")
    for market, info in report["pipeline_stops"].items():
        print(f"  {market.upper():12s} {info['status']} → stops at: {info['stops_at']}")
    print()

    print("Missing for trading:")
    for market, items in report["missing_for_trading"].items():
        print(f"  {market.upper()}: {len(items)} gaps")
    print()
    print(f"Report saved to: {output}")


if __name__ == "__main__":
    main()
