"""OSIRIS Symbol Registry — normalize all provider-specific symbols to canonical form.

Resolves:
  - Duplicate symbols (EURUSD=X vs EURUSD)
  - Provider-specific ambiguity (GC=F vs GOLD)
  - Cross-market symbol collisions (XRP crypto vs XRP stock)

Each entry maps a CANONICAL_SYMBOL to its known aliases and metadata.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from core.schemas.event_schema import AssetClass


@dataclass(frozen=True)
class SymbolEntry:
    canonical: str
    asset_class: AssetClass
    exchange: Optional[str]
    provider_formats: List[str]
    aliases: List[str] = field(default_factory=list)
    name: str = ""
    currency: str = "USD"


SYMBOL_REGISTRY: dict[str, SymbolEntry] = {
    # ── Crypto ──────────────────────────────────────────────────
    "BTC": SymbolEntry(
        canonical="BTC", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["BTCUSDT", "BTC", "bitcoin"],
        aliases=["XBT"], name="Bitcoin",
    ),
    "ETH": SymbolEntry(
        canonical="ETH", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["ETHUSDT", "ETH"],
        aliases=[], name="Ethereum",
    ),
    "SOL": SymbolEntry(
        canonical="SOL", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["SOLUSDT", "SOL"],
        aliases=[], name="Solana",
    ),
    "XRP": SymbolEntry(
        canonical="XRP", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["XRPUSDT", "XRP"],
        aliases=[], name="XRP",
    ),
    "BNB": SymbolEntry(
        canonical="BNB", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["BNBUSDT", "BNB"],
        aliases=[], name="BNB",
    ),
    "ADA": SymbolEntry(
        canonical="ADA", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["ADAUSDT", "ADA"],
        aliases=[], name="Cardano",
    ),
    "DOGE": SymbolEntry(
        canonical="DOGE", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["DOGEUSDT", "DOGE"],
        aliases=[], name="Dogecoin",
    ),
    "AVAX": SymbolEntry(
        canonical="AVAX", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["AVAXUSDT", "AVAX"],
        aliases=[], name="Avalanche",
    ),
    "LINK": SymbolEntry(
        canonical="LINK", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["LINKUSDT", "LINK"],
        aliases=[], name="Chainlink",
    ),
    "MATIC": SymbolEntry(
        canonical="MATIC", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["MATICUSDT", "MATIC"],
        aliases=[], name="Polygon",
    ),
    "DOT": SymbolEntry(
        canonical="DOT", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["DOTUSDT", "DOT"],
        aliases=[], name="Polkadot",
    ),
    "UNI": SymbolEntry(
        canonical="UNI", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["UNIUSDT", "UNI"],
        aliases=[], name="Uniswap",
    ),
    "LTC": SymbolEntry(
        canonical="LTC", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["LTCUSDT", "LTC"],
        aliases=[], name="Litecoin",
    ),
    "BCH": SymbolEntry(
        canonical="BCH", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["BCHUSDT", "BCH"],
        aliases=[], name="Bitcoin Cash",
    ),
    "ATOM": SymbolEntry(
        canonical="ATOM", asset_class=AssetClass.CRYPTO, exchange="Binance",
        provider_formats=["ATOMUSDT", "ATOM"],
        aliases=[], name="Cosmos",
    ),
    # ── Forex ───────────────────────────────────────────────────
    "EURUSD": SymbolEntry(
        canonical="EURUSD", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["EURUSD=X", "EURUSD"],
        aliases=[], name="Euro / US Dollar",
    ),
    "GBPUSD": SymbolEntry(
        canonical="GBPUSD", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["GBPUSD=X", "GBPUSD"],
        aliases=[], name="British Pound / US Dollar",
    ),
    "USDJPY": SymbolEntry(
        canonical="USDJPY", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["USDJPY=X", "USDJPY"],
        aliases=[], name="US Dollar / Japanese Yen",
    ),
    "USDCHF": SymbolEntry(
        canonical="USDCHF", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["USDCHF=X", "USDCHF"],
        aliases=[], name="US Dollar / Swiss Franc",
    ),
    "AUDUSD": SymbolEntry(
        canonical="AUDUSD", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["AUDUSD=X", "AUDUSD"],
        aliases=[], name="Australian Dollar / US Dollar",
    ),
    "USDCAD": SymbolEntry(
        canonical="USDCAD", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["USDCAD=X", "USDCAD"],
        aliases=[], name="US Dollar / Canadian Dollar",
    ),
    "NZDUSD": SymbolEntry(
        canonical="NZDUSD", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["NZDUSD=X", "NZDUSD"],
        aliases=[], name="New Zealand Dollar / US Dollar",
    ),
    "EURGBP": SymbolEntry(
        canonical="EURGBP", asset_class=AssetClass.FOREX, exchange="Forex",
        provider_formats=["EURGBP=X", "EURGBP"],
        aliases=[], name="Euro / British Pound",
    ),
    # ── Stocks ──────────────────────────────────────────────────
    "AAPL": SymbolEntry(
        canonical="AAPL", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["AAPL"],
        aliases=["Apple"], name="Apple Inc.",
    ),
    "MSFT": SymbolEntry(
        canonical="MSFT", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["MSFT"],
        aliases=[], name="Microsoft Corporation",
    ),
    "GOOGL": SymbolEntry(
        canonical="GOOGL", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["GOOGL"],
        aliases=["GOOG"], name="Alphabet Inc.",
    ),
    "AMZN": SymbolEntry(
        canonical="AMZN", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["AMZN"],
        aliases=[], name="Amazon.com Inc.",
    ),
    "TSLA": SymbolEntry(
        canonical="TSLA", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["TSLA"],
        aliases=[], name="Tesla Inc.",
    ),
    "NVDA": SymbolEntry(
        canonical="NVDA", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["NVDA"],
        aliases=[], name="NVIDIA Corporation",
    ),
    "META": SymbolEntry(
        canonical="META", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["META"],
        aliases=[], name="Meta Platforms Inc.",
    ),
    "NFLX": SymbolEntry(
        canonical="NFLX", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["NFLX"],
        aliases=[], name="Netflix Inc.",
    ),
    "AMD": SymbolEntry(
        canonical="AMD", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["AMD"],
        aliases=[], name="Advanced Micro Devices Inc.",
    ),
    "INTC": SymbolEntry(
        canonical="INTC", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["INTC"],
        aliases=[], name="Intel Corporation",
    ),
    "CRM": SymbolEntry(
        canonical="CRM", asset_class=AssetClass.STOCK, exchange="NYSE",
        provider_formats=["CRM"],
        aliases=[], name="Salesforce Inc.",
    ),
    "ADBE": SymbolEntry(
        canonical="ADBE", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["ADBE"],
        aliases=[], name="Adobe Inc.",
    ),
    "PYPL": SymbolEntry(
        canonical="PYPL", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["PYPL"],
        aliases=[], name="PayPal Holdings Inc.",
    ),
    "UBER": SymbolEntry(
        canonical="UBER", asset_class=AssetClass.STOCK, exchange="NYSE",
        provider_formats=["UBER"],
        aliases=[], name="Uber Technologies Inc.",
    ),
    "COIN": SymbolEntry(
        canonical="COIN", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["COIN"],
        aliases=[], name="Coinbase Global Inc.",
    ),
    "PLTR": SymbolEntry(
        canonical="PLTR", asset_class=AssetClass.STOCK, exchange="NYSE",
        provider_formats=["PLTR"],
        aliases=[], name="Palantir Technologies Inc.",
    ),
    # ── ETFs (classified as STOCK for pipeline purposes) ────────
    "SPY": SymbolEntry(
        canonical="SPY", asset_class=AssetClass.STOCK, exchange="NYSE Arca",
        provider_formats=["SPY"],
        aliases=[], name="SPDR S&P 500 ETF Trust",
    ),
    "QQQ": SymbolEntry(
        canonical="QQQ", asset_class=AssetClass.STOCK, exchange="NASDAQ",
        provider_formats=["QQQ"],
        aliases=[], name="Invesco QQQ Trust",
    ),
    "IWM": SymbolEntry(
        canonical="IWM", asset_class=AssetClass.STOCK, exchange="NYSE Arca",
        provider_formats=["IWM"],
        aliases=[], name="iShares Russell 2000 ETF",
    ),
    "DIA": SymbolEntry(
        canonical="DIA", asset_class=AssetClass.STOCK, exchange="NYSE Arca",
        provider_formats=["DIA"],
        aliases=[], name="SPDR Dow Jones Industrial Average ETF",
    ),
    "VTI": SymbolEntry(
        canonical="VTI", asset_class=AssetClass.STOCK, exchange="NYSE Arca",
        provider_formats=["VTI"],
        aliases=[], name="Vanguard Total Stock Market ETF",
    ),
    "VOO": SymbolEntry(
        canonical="VOO", asset_class=AssetClass.STOCK, exchange="NYSE Arca",
        provider_formats=["VOO"],
        aliases=[], name="Vanguard S&P 500 ETF",
    ),
    # ── Commodities ─────────────────────────────────────────────
    "XAU": SymbolEntry(
        canonical="XAU", asset_class=AssetClass.COMMODITY, exchange="COMEX",
        provider_formats=["GC=F", "GOLD"],
        aliases=["GOLD"], name="Gold Futures",
        currency="USD",
    ),
    "XAG": SymbolEntry(
        canonical="XAG", asset_class=AssetClass.COMMODITY, exchange="COMEX",
        provider_formats=["SI=F", "SILVER"],
        aliases=["SILVER"], name="Silver Futures",
        currency="USD",
    ),
    "CL": SymbolEntry(
        canonical="CL", asset_class=AssetClass.COMMODITY, exchange="NYMEX",
        provider_formats=["CL=F", "OIL", "CRUDE_OIL"],
        aliases=["OIL", "CRUDE"], name="Crude Oil Futures",
        currency="USD",
    ),
    "NG": SymbolEntry(
        canonical="NG", asset_class=AssetClass.COMMODITY, exchange="NYMEX",
        provider_formats=["NG=F"],
        aliases=["NATURAL_GAS"], name="Natural Gas Futures",
        currency="USD",
    ),
    "HG": SymbolEntry(
        canonical="HG", asset_class=AssetClass.COMMODITY, exchange="COMEX",
        provider_formats=["HG=F"],
        aliases=["COPPER"], name="Copper Futures",
        currency="USD",
    ),
    "ZW": SymbolEntry(
        canonical="ZW", asset_class=AssetClass.COMMODITY, exchange="CBOT",
        provider_formats=["ZW=F"],
        aliases=["WHEAT"], name="Wheat Futures",
        currency="USD",
    ),
    "ZC": SymbolEntry(
        canonical="ZC", asset_class=AssetClass.COMMODITY, exchange="CBOT",
        provider_formats=["ZC=F"],
        aliases=["CORN"], name="Corn Futures",
        currency="USD",
    ),
    "ZS": SymbolEntry(
        canonical="ZS", asset_class=AssetClass.COMMODITY, exchange="CBOT",
        provider_formats=["ZS=F"],
        aliases=["SOYBEAN"], name="Soybean Futures",
        currency="USD",
    ),
    # ── Indices ─────────────────────────────────────────────────
    "SPX": SymbolEntry(
        canonical="SPX", asset_class=AssetClass.INDEX, exchange="S&P",
        provider_formats=["^GSPC", "SPX"],
        aliases=["S&P 500"], name="S&P 500 Index",
    ),
    "IXIC": SymbolEntry(
        canonical="IXIC", asset_class=AssetClass.INDEX, exchange="NASDAQ",
        provider_formats=["^IXIC"],
        aliases=["NASDAQ"], name="NASDAQ Composite Index",
    ),
    "DJI": SymbolEntry(
        canonical="DJI", asset_class=AssetClass.INDEX, exchange="DJI",
        provider_formats=["^DJI"],
        aliases=["DOW"], name="Dow Jones Industrial Average",
    ),
    "RUT": SymbolEntry(
        canonical="RUT", asset_class=AssetClass.INDEX, exchange="NYSE",
        provider_formats=["^RUT"],
        aliases=["RUSSELL 2000"], name="Russell 2000 Index",
    ),
    "VIX": SymbolEntry(
        canonical="VIX", asset_class=AssetClass.INDEX, exchange="CBOE",
        provider_formats=["^VIX"],
        aliases=["VOLATILITY"], name="CBOE Volatility Index",
    ),
    "FTSE": SymbolEntry(
        canonical="FTSE", asset_class=AssetClass.INDEX, exchange="LSE",
        provider_formats=["^FTSE"],
        aliases=["UK100"], name="FTSE 100 Index",
        currency="GBP",
    ),
    "N225": SymbolEntry(
        canonical="N225", asset_class=AssetClass.INDEX, exchange="TSE",
        provider_formats=["^N225"],
        aliases=["NIKKEI"], name="Nikkei 225 Index",
        currency="JPY",
    ),
    "HSI": SymbolEntry(
        canonical="HSI", asset_class=AssetClass.INDEX, exchange="HKEX",
        provider_formats=["^HSI"],
        aliases=["HANG SENG"], name="Hang Seng Index",
        currency="HKD",
    ),
    # ── Bonds ───────────────────────────────────────────────────
    "DGS10": SymbolEntry(
        canonical="DGS10", asset_class=AssetClass.BOND, exchange="FRED",
        provider_formats=["DGS10"],
        aliases=["US10Y"], name="10-Year Treasury Constant Maturity Rate",
    ),
    "DGS2": SymbolEntry(
        canonical="DGS2", asset_class=AssetClass.BOND, exchange="FRED",
        provider_formats=["DGS2"],
        aliases=["US2Y"], name="2-Year Treasury Constant Maturity Rate",
    ),
    "T10Y2Y": SymbolEntry(
        canonical="T10Y2Y", asset_class=AssetClass.BOND, exchange="FRED",
        provider_formats=["T10Y2Y"],
        aliases=["10Y2Y_SPREAD"], name="10-Year minus 2-Year Treasury Yield Spread",
    ),
    "DFF": SymbolEntry(
        canonical="DFF", asset_class=AssetClass.BOND, exchange="FRED",
        provider_formats=["DFF"],
        aliases=["FED_FUNDS"], name="Effective Federal Funds Rate",
    ),
}


def lookup(candidate: str) -> SymbolEntry | None:
    """Resolve a raw provider symbol to its canonical SymbolEntry.

    Matches against provider_formats, canonical symbol, and aliases.
    Returns None if no match is found.
    """
    normalized = candidate.strip().upper()
    for entry in SYMBOL_REGISTRY.values():
        if entry.canonical == normalized:
            return entry
        if any(f.upper() == normalized for f in entry.provider_formats):
            return entry
        if any(a.upper() == normalized for a in entry.aliases):
            return entry
    return None


def from_canonical(canonical: str) -> SymbolEntry | None:
    entry = SYMBOL_REGISTRY.get(canonical.upper())
    if entry is not None and entry.canonical == canonical.upper():
        return entry
    for e in SYMBOL_REGISTRY.values():
        if e.canonical == canonical.upper():
            return e
    return None


def asset_class_for_symbol(symbol: str) -> str | None:
    entry = lookup(symbol)
    if entry is None:
        return None
    return entry.asset_class.value
