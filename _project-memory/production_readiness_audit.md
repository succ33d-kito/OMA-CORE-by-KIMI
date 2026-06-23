# OSIRIS Production Readiness Audit — Phase 10

## Summary

| Tier | Ready? | Key Risk | Action Required |
|------|--------|----------|-----------------|
| **Paper Trading** | **YES** | Favorable-window bias | Run 60 days across 3 market regimes |
| **Demo Capital** | **NO** | SHORT signal structurally broken | Replace RSI>70 with MomentumBreakdown |
| **Real Capital** | **NO** | No bearish test data | Wait for regime shift or synthetically verify |

---

## Tier 1: Paper Trading Readiness

### Evidence
- 91 tests passing
- SlippageEngine (entry/exit/spread) integrated and tested
- DirectionController: rolling 20-trade WR per direction, disabled LONG at WR<25%
- CapitalGuard: max daily/weekly loss, max open risk, kill switch
- Position sizing: risk_base grows 0.1%/trade (realistic compounding cap)

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 97.8% WR is a regime artifact, not alpha | High | Critical — false confidence | Verify on multiple windows |
| SHORT untested in current window | High | Medium — paper only | Wait for mixed window or backtest on older data |
| CapitalGuard daily/weekly loss untriggered | Medium | Low — paper only | No Upt loss occurred; logic is unit-tested |
| DirectionController disabled LONG correctly | Low | Medium — paper only | Verified: 833 trades blocked |

### Go/No-Go: **GO** for paper trading
Paper trading is low-risk. Start immediately. Run for 60 continuous days across 3+ market regimes. Log all metrics. Do not intervene.

### Recommended Config
```
slippage: 0.10% + spread (BTC=1bps, ETH=2bps, SOL=3bps)
direction_controller: enabled (window=20, wr_threshold=0.25)
capital_guard: enabled (max_daily=10%, max_weekly=20%, max_open_risk=25%)
signal_mode: both
position_sizing: risk_base (0.1%/trade growth cap)
```

---

## Tier 2: Demo Capital Readiness

### Gaps vs Paper

| Gap | Severity | Fix |
|-----|----------|-----|
| SHORT signal (RSI>70) has PF=0.26-0.40 | **CRITICAL** | Replace with MomentumBreakdown (PF=1.50) |
| No bearish window test | High | Wait for regime shift or inject synthetic bad data |
| 97.8% WR may not persist | High | Lower conviction threshold; expect 60-70% WR in mixed market |
| Conviction has no within-direction predictive power (r=-0.465) | Medium | Accept limitation; conviction works across directions (Top 10% = 92.6% WR) |

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SHORT enters losing streak due to RSI>70 | Very High | High — 50% of capital exposed | DirectionController would disable SHORT after 5 losing trades, but each loss is ~2% |
| Regime shift from bull to bear while LONG_ONLY | Medium | High — no SHORT protection | DirectionController re-enables SHORT when WR recovers above 35% |
| CapitalGuard kill switch not tested in market stress | Low | Medium | Unit test passed; logic verified |

### Go/No-Go: **NO** for demo capital
Blocking issue: SHORT signal (RSI>70) is structurally broken. Fix required:
1. Replace RSI>70 with MomentumBreakdown in MarketAgent
2. Verify on a mixed-direction window
3. Run paper trading for minimum 2 weeks with new signal

---

## Tier 3: Real Capital Readiness

### Gaps vs Demo

| Gap | Severity | Fix |
|-----|----------|-----|
| No real-market validation | **ABSOLUTE** | Minimum 60 days demo capital required |
| No operational procedures | High | Define: startup, shutdown, emergency stop, daily review |
| No monitoring/alerting | High | Build: PnL tracker, DD alerts, kill switch API |
| No broker integration | High | Build: exchange connector, order management |
| No legal/compliance review | High | Only relevant for real capital |

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Black swan event destroys capital | Low | Absolute | CapitalGuard max 25% open risk, daily 10% stop |
| API outage causes missed SL/TP | Medium | High — gap risk | Exchange connector must handle WS disconnect |
| Slippage exceeds model during volatility | Medium | Medium — costs spike | SlippageEngine uses static BPS; during vol, actual slippage may be 2-5x |
| Position sizing rule fails in live market | Low | Medium | risk_base cap prevents runaway sizing |
| Human error (fat finger, config mistake) | Medium | Low — demo only | Require 2-person review for real capital config changes |

### Go/No-Go: **NO** for real capital
Prerequisites (in order):
1. Fix SHORT signal (MomentumBreakdown replacement)
2. 60 days paper trading across 3 regimes
3. 60 days demo capital with >0% return and <20% max DD
4. Broker connector built and integration-tested
5. Monitoring and alerting system
6. Legal/compliance sign-off
7. 2-person review for all config changes

---

## Outstanding Issues

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| FLAW-7 | Capital tracking bug (FIXED) | Critical | Fixed in PaperTradingEngine |
| FLAW-8 | SHORT systematically loses (PF=0.26) | Critical | Diagnosed; root cause = RSI>70 mean reversion |
| FLAW-9 | No slippage model (FIXED) | High | Fixed: SlippageEngine + spread |
| FLAW-10 | Conviction no single-direction predictive power | Medium | Accepted limitation |
| FLAW-11 | No bearish window test data | High | Pending — need market regime shift |
| FLAW-12 | 97.8% WR may be regime artifact | High | Only 2 windows tested (both uptrend) |

---

## Decision: Path Forward

```
Current:   Paper Trading Ready (tier 1)
           └── Fix SHORT signal (MomentumBreakdown)
               └── Verify mixed-direction window
                   └── Demo Capital Ready (tier 2)
                       └── 60 days demo + monitoring
                           └── Real Capital Ready (tier 3)
```

**Recommended immediate actions:**
1. Replace RSI>70 with MomentumBreakdown in MarketAgent SHORT signal
2. Continue paper trading; wait for mixed-direction window
3. When mixed window appears: re-run Phase 8 with new SHORT signal
4. After 2 weeks verified: move to demo capital (tier 2)
