# Multi-Market Audit

| Market | Module | Observation | Reasoning | Signal generation | Council | Execution | Risk | Paper trading | Production readiness |
|---|---|---|---|---|---|---|---|---|---|
| Crypto | `core/markets/crypto.py`, Binance/CoinGecko collectors | Best represented | Heuristic/collector-backed | Partial | Generic council | Experimental | Partial guards | Exists | Not ready |
| Forex | `core/markets/forex.py` | Structural support | Limited evidence | Partial | Generic council | Not certified | Partial | Unclear | Not ready |
| Stocks | `core/markets/stocks.py`, Yahoo collector | Structural + data support | Better than most non-crypto | Partial | Generic council | Not certified | Partial | Unclear | Not ready |
| Commodities | `core/markets/commodities.py` | Structural support | Limited evidence | Partial | Generic council | Not certified | Partial | Unclear | Not ready |
| Indices | `core/markets/indices.py` | Structural support | Limited evidence | Partial | Generic council | Not certified | Partial | Unclear | Not ready |
| Bonds | `core/markets/bonds.py` | Structural support | Minimal evidence | Partial | Generic council | Not certified | Partial | Unclear | Not ready |

## Cross-market conclusion

The repository has multi-market aspiration and structural modules, but production-grade market-specific observation, reasoning, execution, risk, and paper-trading validation are not certified per market.
