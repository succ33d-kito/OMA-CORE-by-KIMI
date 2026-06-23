# OSIRIS Demo Deployment Plan

## Phase 5 — Demo Mode Specification

---

### 1. Exchange / Broker Choice

**Primary: Binance (Spot)**
- API provides USDT-margined spot trading
- Matches existing OHLCV data source
- Low latency, high liquidity
- No leverage in demo mode

**Secondary: Bybit / Kraken**
- Fallback if Binance API unavailable
- Same instrument pairs (BTCUSDT, ETHUSDT, SOLUSDT)

**Rule**: Use the exchange that matches the data source. OSIRIS is calibrated on Binance 1h candles. Switching exchanges introduces execution mismatch.

### 2. API Key Safety

| Security Measure | Implementation |
|---|---|
| Read-only keys | API key with ONLY `read` permission. No trade/sell permissions. |
| Dedicated demo account | Separate sub-account for OSIRIS. Main account never exposed. |
| IP whitelisting | Restrict API key to deployment server IP only. |
| Key storage | Environment variables only. Never in code, never in git. |
| Key rotation | Rotate API key every 30 days of demo. |
| Rate limiting | Max 10 requests/second. Binance limits are 1200/ minute. |
| Error handling | On API error: skip candle, log warning, never crash. |

### 3. Read-Only First

**Week 1-2**: Read-only mode
- Fetch OHLCV data via API
- Generate signals via MarketAgent + Council
- Log all trade decisions to file
- Compare paper execution vs what would have been executed on exchange
- Measure slippage delta between simulated and real fills

**Week 2-4**: Paper/demo execution
- Place orders on exchange demo/paper endpoints
- Track fills, slippage, rejections
- No real capital at risk

### 4. Execution Configuration

| Parameter | Demo Value | Rationale |
|---|---|---|
| Initial capital | $10,000 (paper) | Matches all backtest configurations |
| Max open positions | 3 | Reduced from 5 for safety |
| Max position size | 5% per trade | Reduced from 20% in backtest |
| Max daily loss | 5% | Tightened from 10% |
| Max weekly loss | 10% | Tightened from 20% |
| Slippage model | 10bps + asset spread | Matches reality_test.py |
| ATR stop multiplier | 3.0 | Proven across 8 regimes |
| Short style | combined | Best from A/B testing |

### 5. Order Types

| Action | Order Type | Rationale |
|---|---|---|
| Entry | LIMIT (post-only) | Avoid taker fees. Use signal price + slippage. |
| Stop loss | STOP_MARKET | Exit at market if price breaches stop. |
| Take profit | LIMIT | Exit at target price. Post-only. |
| Emergency exit | MARKET | Only in EMERGENCY/PANIC crash mode. |

### 6. Manual Override

```
Manual Override Protocol:
1. Human monitor receives Telegram alert
2. Can issue override commands via /stop, /reduce, /resume
3. Override persists until manually cleared
4. All overrides logged to audit file
5. Remote kill switch: set KILL=1 in environment → OSIRIS exits all positions
```

**Override commands:**
- `/stop` — Close all positions, disable entry, kill switch ON
- `/reduce N` — Reduce position sizing to N% of normal
- `/resume` — Clear all overrides, return to normal operation
- `/status` — Print portfolio summary to Telegram
- `/positions` — Print open positions to Telegram

### 7. Telegram Risk Alerts

**Alert channels:**
1. **OSIRIS-ALERTS** — Critical only (kill switch, emergency mode, drawdown breach)
2. **OSIRIS-DAILY** — Daily summary (PnL, trades, open positions, guard states)
3. **OSIRIS-RAW** — Every trade executed (entry, exit, SL, TP, PnL)

**Alert triggers:**
| Trigger | Channel | Format |
|---|---|---|
| New trade opened | RAW | `{asset} {dir} @ {price} SL {sl} TP {tp}` |
| Trade closed | RAW | `{asset} {dir} {exit_reason} PnL {pnl}%` |
| Daily loss > 3% | ALERTS | `⚠ Daily loss {pct}% — approaching 5% limit` |
| Daily loss > 5% | ALERTS | `🚨 Daily loss limit hit — disabling entries` |
| Weekly loss > 10% | ALERTS | `🚨 Weekly loss limit hit — disabling entries` |
| Enter EMERGENCY mode | ALERTS | `🚨 EMERGENCY MODE — DD {dd}% — reducing to 25%` |
| Enter HALT mode | ALERTS | `🔥 HALT — DD {dd}% — kill switch active` |
| CrashDetector PANIC | ALERTS | `🔥 CRASH PANIC — score {score} — closing all` |
| Kill switch activated | ALERTS | `💀 KILL SWITCH ON — all positions closed` |
| Daily summary | DAILY | `📊 {date} | Return {ret}% | DD {dd}% | Trades {n} | Guard {mode}` |

### 8. Kill Switch Architecture

```
Kill Switch (automated):
- CapitalGuard: 35% drawdown → HALT mode → deactivate_kill_switch()
- CrashDetector: PANIC mode → position_size_multiplier() → 0.0 (no new entries)
- Manual: /stop command → kill switch ON

Kill Switch (manual):
- Remote file: /tmp/osiris_kill (touch file to activate)
- Environment: KILL=1 (set env var to activate)
- Telegram: /stop command

Kill switch recovery:
- Cannot auto-recover
- Requires human verification of market conditions
- Manual /resume command or KILL=0
- Recovery protocol: 10 profitable trades before full sizing
```

### 9. Monitoring Dashboard

**File-based monitoring (no new infrastructure):**
```
_project-memory/demo_log/
├── trades/          — CSV of all trades
├── guards/          — Guard activation log per day
├── daily/           — Daily portfolio summary
├── alerts/          — Alert log
└── status.json      — Current system state (updated every hour)
```

**Status.json format:**
```json
{
  "timestamp": "2026-06-22T23:00:00Z",
  "mode": "demo",
  "equity": 10050.00,
  "open_positions": 2,
  "total_trades": 45,
  "win_rate": 55.0,
  "guard_mode": "normal",
  "crash_mode": "none",
  "kill_switch": false,
  "last_alert": null,
  "uptime_hours": 168
}
```

### 10. Deployment Timeline

```
Week 1: Read-only API integration
  - Connect to Binance API
  - Verify OHLCV matches backtest data
  - Log paper signals vs real exchange prices
  - No orders placed

Week 2: Paper execution
  - Enable paper trading on Binance testnet
  - Run 7-day paper test with reduced sizing
  - Monitor guard activations
  - Validate slippage model

Week 3: Guard stress test
  - Manually verify each guard triggers correctly
  - Test kill switch (touch /tmp/osiris_kill)
  - Test Telegram alerts
  - Fix any issues found

Week 4: Conditional demo activation
  - All guards verified
  - Kill switch tested
  - 7+ days of paper trading without issues
  - Demo Gate checklist 90%+ passed
  - FINAL GO/NO-GO decision
```

### 11. Risk Limits

| Risk Parameter | Demo Value | Notes |
|---|---|---|
| Max single trade loss | $200 (2%) | At $10k capital |
| Max daily loss | $500 (5%) | Hard stop |
| Max weekly loss | $1,000 (10%) | Hard stop |
| Max open risk | $2,500 (25%) | Across all positions |
| Max correlated exposure | 40% | Same-asset limit |
| Min time between trades | 1 hour | Avoid revenge trading |
| Max trades per day | 10 | Position management limit |
| Max drawdown before halt | 35% | Kill switch triggers |
