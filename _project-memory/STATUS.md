# Status — 2026-06-22 (end of session 8 — Extended Paper Trading & Demo Gate Sprint)

## What Exists (Functional)

### Data Layer
- [x] 7 collectors (CoinGecko, YahooFinance, Binance, FRED, RSS, Sentiment, Polymarket)
- [x] WorldMonitorV2 — orchestrates all collectors, publishes to EventBus
- [x] Scoring engine — 6 components (urgency, sentiment, source, relevance, recency, correlation)
- [x] Opportunity engine — 24 types, 13 action templates
- [x] Data quality engine — 7 validation checks
- [x] SQLite + PostgreSQL — non-destructive migration

### OSIRIS Agent Architecture ✓ (session 1)
- [x] ACP schema — AgentOpinion, CouncilDecision, AgentRole, Recommendation
- [x] EventBus — pub/sub with 10 topics, history buffer
- [x] Agent Council — consensus engine (conviction, consensus, disagreement)
- [x] MetaCouncil — Trader/Entrepreneur/Creator comparison
- [x] NewsAgent — rule-based news/geo/regulatory analysis
- [x] MacroAgent — rule-based macro/earnings/merger analysis (30+ indicators)

### Trading Autonomous System ✓ (session 2)
- [x] TradeSignal schema — position_size_pct, take_profit, stop_loss, risk_reward_ratio
- [x] MarketAgent — OHLCV indicators (RSI, ATR, SMA20/50, momentum, trend), price metadata
- [x] RiskAgent — scenario risk by event type (hack=0.35, geo=0.25), volatility-based risk, position sizing
- [x] AgentCouncil v2 — EMA track record (α=0.1), weighted vote, 95% CI conviction, risk 25% weight
- [x] BacktestEngineV2 — real OHLCV (Binance+yfinance), candle-by-candle SL/TP, 7 metrics
- [x] PaperTradingEngine — signal→position, slippage/spread, DirectionController, CapitalGuard
- [x] PerformanceMemory — agent track records, confidence calibration, by-asset/by-direction P&L
- [x] **SlippageEngine** — entry/exit/stop/target price adjustment + per-asset spread (BTC=1bps, ETH=2bps, SOL=3bps)
- [x] **DirectionController** — rolling 20-trade WR per direction, auto-disable at <25% WR
- [x] **CapitalGuard** — max daily 10% loss, max weekly 20% loss, max open risk 25%, kill switch, GuardMode (NORMAL/CAUTION/EMERGENCY/HALT), drawdown tracking, consecutive loss tracking
- [x] **CrashDetector** — drawdown velocity, gap size, ATR expansion, volume spike, crash score, CrashMode (NONE/WARNING/EMERGENCY/PANIC), position_size_multiplier
- [x] **KnifeDetector** — dip vs falling knife detection via bounce quality, volume profile, momentum, volatility contraction
- [x] **GapRiskEngine** — gap risk score 0-100, stop cushion multiplier, size reduction based on historical gap size, weekend/overnight risk, liquidation cascade risk

### User System ✓ (session 1)
- [x] UserProfile model — typed, serializable
- [x] TraderPreferences, EntrepreneurPreferences, CreatorPreferences
- [x] ProfileRegistry — CRUD + DB persistence

### Memory ✓ (session 1)
- [x] ShortTermMemory — TTL-based, max-size, search
- [x] LongTermMemory — tag-based, access-count tracking
- [x] MemoryStore — event-keyed opinion cache

### Infrastructure ✓ (sessions 1+2)
- [x] OSIRISConfig — centralized env-based config
- [x] Fixed CLI — uses WorldMonitorV2 (all 7 collectors), adds `council` command
- [x] Fixed migration — non-destructive upsert (was DROP + recreate)
- [x] Deprecated world_monitor.py — marked with DeprecationWarning
- [x] Tests — 91 passing (was 62)
- [x] Project Memory — 5 files in `_project-memory/`

### Validation ✓ (session 3)
- [x] Full system audit — risk matrix for all 7 trading components
- [x] 5 critical pipeline bugs fixed (C1-C3, H1, H4)
- [x] 17 integration tests — end-to-end pipeline verified
- [x] 14-day paper trading experiment with real Binance data (1,365 events, 292 trades)
- [x] Agent performance attribution — both agents 7.5% accuracy, severely overconfident
- [x] Council validation — conviction r≈+0.036 (predictive), consensus 0% discriminatory power
- [x] Production readiness assessment — Paper Trading: 60%, Demo: 30%, Real Capital: 0%

### Recovery Sprint ✓ (session 4)
- [x] RiskAgent dynamic confidence (0.30-0.85) + WATCH default (removed structural BUY bias)
- [x] Council WATCH-ignore — non-directional votes don't block actionable recommendations
- [x] TrendAgent built (EMA-based, 3rd vote) — tested, adds noise in current config
- [x] ATR×3.0 optimal stop for crypto (both directions enabled)
- [x] `signal_mode` parameter on MarketAgent (both/short_only/long_only)
- [x] Experiment harness fix — ATR override now correctly adjusts both stop_loss and take_profit
- [x] SHORT-only confirmed at 89.2% WR, +277.24% in choppy markets
- [x] BOTH directions confirmed at 61.9% WR, +514.63% over 60 days
- [x] System recovered from -123% to +514% — **637 pp improvement**

### Research Sprint ✓ (session 5)
- [x] **Phase 1 — Robustness**: Alpha persists across 30/60/90 days ✓. 30d: +37.9% (most recent/relevant)
- [x] **Phase 2 — Regime Analysis**: Alpha is regime-dependent. LONG wins 78% in uptrends (PF=11.02). SHORT loses 78% (PF=0.26).
- [x] **Phase 3 — LONG/SHORT Attribution**: LONG = alpha engine (PF=11.02). SHORT = alpha destroyer (PF=0.26).
- [x] **Phase 4 — Conviction Validation**: Top 10% conviction = 92.6% WR. No within-direction power (r=-0.465 in all-LONG regime).
- [x] **Phase 5 — Agent Attribution**: MarketAgent = alpha. RiskAgent = veto. Both needed.
- [x] **Phase 6 — Regime Detection Design**: Two-level adaptive bias proposed.
- [x] **Capital tracking bug**: FLAW-7 fixed. All prior absolute returns overstated.

### Alpha Realism Sprint ✓ (session 6)
- [x] **Phase 1 — Slippage Reality Layer**: SlippageEngine implemented. Tested 0.05%/0.10%/0.25%/0.50%.
- [x] **Phase 2 — Spread Model**: Per-asset bid/ask spread on entry/exit (BTC=1bps, ETH=2bps, SOL=3bps).
- [x] **Phase 3 — Alpha Survival Test**: 30d/60d at 0%/0.10%/0.25%. Even 0.25% slippage leaves PF=3.38.
- [x] **Phase 4 — SHORT Reconstruction**: MomentumBreakdown (PF=1.50) vs RSI>75 (PF=0.04).
- [x] **Phase 5 — Direction Bias Controller**: Rolling 20-trade WR per direction.
- [x] **Phase 6 — Regime Discovery**: Blocked — no bearish/sideways window in available data.
- [x] **Phase 7 — Capital Protection Layer**: Max daily 10%/weekly 20%/open risk 25%.
- [x] **Phase 8 — Paper Trading Reality Test**: 30d: +783.76% (97.8% WR). 60d: +1289.88% (98.5% WR).
- [x] **Phase 9 — Alpha Attribution**: Blocked.
- [x] **Phase 10 — Production Readiness Audit**: Paper: GO. Demo: NO (SHORT signal broken). Real: NO.

### Regime Robustness Sprint ✓ (session 7 — NEW)
- [x] **Phase 1 — Bear Market Validation**: 3/4 survive. COVID gap-down fails (-6.64%). May 2021 (+2114%), Luna (+11183%), FTX (+1041%) survive.
- [x] **Phase 2 — Sideways Market Validation**: 2/2 survive. Post-FTX Range (+6755%), Mid-2023 Consolidation (+46.76%).
- [x] **Phase 3 — Volatility Regime Testing**: 98% of trades in high-vol. System rarely trades in low-vol regimes.
- [x] **Phase 4 — SHORT Replacement A/B**: RSI and MomBreak identical in 4/6 periods (Path A dominates SHORT). MomBreak has `elif` chain bug — blocks RSI<30 BUY signals. **Combined style (RSI OR MomBreak) recommended**.
- [x] **Phase 5 — Direction Controller Validation**: LONG_ONLY ≈ BOTH in bear (system generates 0 SHORT trades). SHORT_ONLY loses everywhere. Current rolling-window approach ineffective (too few SHORT trades to fill 20-trade window).
- [x] **Phase 6 — Failure Analysis**: ONLY failure mode = COVID gap-down crash (no bounces). 5 SHORT trades, all losses. No other failure mode in 7 periods across 3 regimes.
- [x] **Phase 7 — Demo Readiness Assessment**: **87.5% survival across 8 periods**. Demo READY with conditions (gap-down monitoring, tighter CapitalGuard daily loss).
- [x] **Regime report**: `_project-memory/regime_robustness_report.md`
- [x] **`short_style` parameter** added to MarketAgent: "rsi" / "mom_break" / "combined" (default: mom_break)

### Extended Paper Trading & Demo Gate Sprint ✓ (session 8 — NEW)
- [x] **Phase 1 — Extended Paper Trading**: 7-day (+5.60%, 22 SHORT trades, 2.75% DD) and 30-day (-0.58%, 5 SHORT trades, 0.58% DD) runs completed.
- [x] **Phase 2 — Guard Validation**: CapitalGuard (PASS), DirectionController (PASS), CrashDetector (CONDITIONAL — fails multi-day), KnifeDetector (NOT TESTED), GapRiskEngine (PASS), Emergency Mode (CONDITIONAL), Kill Switch (NOT TESTED).
- [x] **Phase 3 — Demo Gate Criteria**: Defined in `_project-memory/demo_gate_checklist.md`. 3 critical blockers identified.
- [x] **Phase 4 — COVID Replay**: Loss CAPPED from -6.64% (no guards) to -3.36% (with guards). 49.4% improvement. Protection from GapRiskEngine + CapitalGuard + DirectionController (NOT CrashDetector — fails multi-day).
- [x] **Phase 5 — Demo Deployment Plan**: Exchanges, API safety, read-only first, order types, manual override, Telegram alerts, kill switch architecture, monitoring dashboard, deployment timeline, risk limits. Documented in `_project-memory/demo_deployment_plan.md`.
- [x] **Phase 6 — Final Recommendation**: Paper=GO, Demo=CONDITIONAL (3 blockers remain), Real=NO.
- [x] **GuardLogger**: Logs every blocked trade with reason, asset, timestamp, direction, would-be size, market condition.
- [x] **Extended paper test script**: `scripts/extended_paper_test.py` — runs 7-day and 30-day paper tests, guard validation, COVID replay. All phases configurable via `--phase`.
- [x] **BTC-only crash/gap tracking**: Fixed multi-asset data contamination bug in CrashDetector and GapRiskEngine. Detectors now only track BTC as market proxy.
- [x] **CapitalGuard emergency mode**: GuardMode enum (NORMAL/CAUTION/EMERGENCY/HALT), drawdown tracking, consecutive loss tracking, can_enter_new_position control.

## Critical Flaws

- ~~[FLAW-1] RiskAgent fixed confidence=0.75~~ → **FIXED**
- ~~[FLAW-2] Consensus deadlock~~ → **MITIGATED**
- ~~[FLAW-3] Stop losses too tight~~ → **FIXED**
- ~~[FLAW-4] Track record effect too weak~~ → **PARTIAL** (low priority)
- ~~[FLAW-5] No short execution~~ → **FIXED**
- **[FLAW-6] In-memory PerformanceMemory**: all agent learning resets every session
- ~~[FLAW-7] Position sizing used initial capital~~ → **FIXED**
- **[FLAW-8] SHORT systematically loses (PF=0.26)**: RSI>70 mean reversion fights trend. MomentumBreakdown (PF=1.50) identified as replacement. `short_style` param added but default still "mom_break". **Combined style recommended**.
- ~~[FLAW-9] No slippage model~~ → **FIXED**
- **[FLAW-10] Conviction no single-direction predictive power**
- ~~[FLAW-11] No bearish window test data~~ → **RESOLVED**: Tested across 4 bear periods. COVID gap-down is the ONLY failure mode.
- ~~[FLAW-12] 97.8% WR may be regime artifact~~ → **CONFIRMED**: Both current windows are strongly uptrending. Regime-dependent.
- **[FLAW-13] DirectionController rolling window ineffective**: SHORT trades too rare to fill 20-trade window. ~0 SHORT trades in most bear periods.
- **[FLAW-14] MomBreak elif chain blocks RSI<30 BUY**: In `elif` chain, momentum breakdown condition fires before RSI<30 → blocks oversold BUY signals in ranging markets.
- **[FLAW-15] COVID gap-down failure**: System produces 0 LONG and 5 losing SHORT trades in straight-line crash. No recovery mechanism.
- **[FLAW-16] CrashDetector no multi-day crash detection**: COVID-style crashes unfold over 48+ hours. 6-hour velocity and hourly gap detectors stay in NONE mode. Need multi-window drawdown velocity (6h, 24h, 72h).
- **[FLAW-17] KnifeDetector untested**: System generated 0 LONG signals across all test windows. Dip vs falling knife logic cannot be verified. Critical for crash protection.
- **[FLAW-18] Kill switch untested**: 35% DD threshold never approached in any test. Cannot verify halt behavior.

## Next Actions

### Immediate (FLAW-16 fix: CrashDetector multi-day detection)
1. **Fix CrashDetector multi-window drawdown velocity**: Add 6h, 24h, and 72h windows to detect both flash and slow crashes.
2. **Run controlled drawdown test**: Force system into 35%+ DD to verify kill switch and HALT mode.
3. **Force LONG signal in test**: Override MarketAgent to generate LONG signal, verify KnifeDetector dip vs falling knife logic.

### Demo Gate Blocker Fixes (must complete before demo activation)
4. **Fix FLAW-16**: Multi-window CrashDetector (6h/24h/72h velocity).
5. **Fix FLAW-17**: KnifeDetector test with forced LONG signal.
6. **Fix FLAW-18**: Kill switch verification through controlled drawdown.

### High Priority
7. **Fix MarketAgent elif chain** (FLAW-14): Separate RSI>70 / momentum breakdown / RSI<30 into independent checks.
8. **Switch short_style default to "combined"**: Both RSI>70 and momentum breakdown for SHORT.
9. **Fix DirectionController** (FLAW-13): Replace rolling 20-trade window with global WR tracking + minimum trade threshold.

### Medium Priority
10. PerformanceMemory persistence (SQLite backend)
11. Kelly position sizing (replace fixed fraction)
12. Multi-asset validation (XRP, BNB, DOGE, AVAX, LINK)
13. OHLCV caching
14. Paper trading (real-time, no intervention) for 30 days — verify regime robustness in current market

### Low Priority
- Entrepreneur Agent, Creator Agent, Execution Agent, Vector DB, CI/CD

## Key Findings — Regime Robustness Sprint (NEW)

### Bear Market Survival: 3/4 (75%)
- **COVID Crash (Mar-Apr 2020)**: FAILED. -6.64%. 5 SHORT trades, all losses. Gap-down crash with no sustained bounces.
- **May 2021 Crash**: SURVIVED. +2114%. 688 LONG + 325 SHORT. System profits from volatile bounces.
- **Luna/3AC Crash**: SURVIVED. +11183%. 99.3% LONG. Captures massive counter-trend bounces.
- **FTX Collapse**: SURVIVED. +1041%. 97% LONG. Same mechanism — buys bounces.
- **Primary survival mechanism**: The system is 68-99% LONG even in bear markets. Wide ATR×3.0 stops + 1:2 RR capture 30-50% counter-trend rallies.

### SHORT A/B Comparison
- RSI>70 and MomBreak produce **identical results in 4/6 periods** (Path A structure-based SHORT dominates).
- MomBreak has a structural bug: the `elif` chain prevents RSI<30 BUY from firing when momentum breakdown fires. In Mid-2023: RSI style = 3846 trades, MomBreak = 58 trades.
- **Recommended**: Use "combined" style (RSI>70 OR momentum breakdown) to maximize both frequency and quality.

### Direction Controller Validation
- LONG_ONLY ≈ BOTH in most bear periods (system generates ~0 SHORT trades).
- SHORT_ONLY loses everywhere (-1.88% to -14.37%). Never profitable alone.
- **DirectionController rolling window is ineffective**: SHORT trades are too rare to fill a 20-trade window. Need alternative approach (global WR tracking or regime-based disabling).

### Only Failure Mode: COVID Gap-Down Crash
- When market drops 50%+ without sustained bounces, the system:
  1. Generates 0 LONG signals (no uptrend detected)
  2. Generates 5 losing SHORT signals (badly timed)
  3. Cannot recover
- No other failure mode identified across 7 historical periods.

### Demo Readiness Updated
- **Previous verdict** (session 6): Paper=GO, Demo=NO, Real=NO
- **New verdict** (session 7): **Demo=YES with conditions**
- Survival rate: 87.5% (7/8 periods)
- Conditions: tighter CapitalGuard (5% daily loss), gap-down monitoring, manual kill switch for crash scenarios

## Key Findings — Alpha Realism Sprint

### SHORT Root Cause
RSI>70 mean reversion has PF=0.04 (ETH) to 0.40 (BTC). MomentumBreakdown (close < low of last 5 candles) has PF=1.23-1.50. EMACrossDown has PF=3.00 (but only 3-5 signals). **The fix is to replace RSI>70 with MomentumBreakdown.**

### Position Sizing Realism
Position sizing previously used `self.capital` (compounding), producing absurd returns ($10k → $16M in 30d). Fixed: `risk_base` grows by 0.1%/trade from initial capital. This caps compounding to: $10k after 736 trades → $17,360 max. Realistic.

### Guard Effectiveness
DirectionController: disabled LONG at 20% WR. Blocked 833 trades. CapitalGuard: never triggered (no daily loss exceeded 10%). The guards work as designed but are untested in bearish conditions.

### Current Market Regime
The May 18 - Jun 22 window is extremely favorable for LONG. 97.8-98.5% WR with 720-1052 TP exits (only 16 SL). This is regime-dependent. The system's true WR in mixed markets is ~68% (from research sprint on earlier window).

### Production Readiness
- **Paper Trading**: GO. All guards operational. Slippage realistic.
- **Demo Capital**: NO. SHORT signal (RSI>70) is structurally broken. Must fix first.
- **Real Capital**: NO. Requires 60 days demo + broker integration + monitoring.

## Key Evidence

### Research Sprint (Session 5)
- **30d corrected return**: +37.9% (after capital tracking fix, was +110%)
- **LONG PF=11.02 in uptrends**: alpha engine
- **SHORT PF=0.26 in uptrends**: alpha destroyer
- **Top 10% conviction = 92.6% WR**: predictive across directions
- **Correlation within direction**: r=-0.465 (not predictive within same direction)

### Alpha Realism Sprint (Session 6)
- **Slippage survival**: At 0.50% + spread, PF=1.59 (alpha survives worst case)
- **MomentumBreakdown SHORT**: PF=1.50, 42.9% WR — viable replacement for RSI>70
- **RSI>75 SHORT**: PF=0.04 (ETH), 3.1% WR — structurally broken
- **DirectionController**: blocked 833 trades after LONG WR dropped to 20%
- **30d reality test**: +783.76% (97.8% WR, 1.26% MaxDD) — favorable window artifact
- **60d reality test**: +1289.88% (98.5% WR, 0.96% MaxDD) — same favorable window

### Recovery Sprint (Session 4)
- **RiskAgent WATCH default**: 33% SHORT trades (was 0%)
- **Council WATCH-ignore**: directional signal now always wins
- **Best config**: BOTH directions, MarketAgent + RiskAgent, ATR×3.0
- **14-day**: +111.01% (45.4% WR, 6.62 Sharpe)
- **30-day**: +395.19% (60.6% WR, 7.58 Sharpe)
- **60-day**: +514.63% (61.9% WR, 7.68 Sharpe)
- **SHORT-only**: 89.2% WR in choppy 14d
- **TrendAgent adds noise**: all 3-agent configs worse

## Open Questions

- **When will a bearish window appear?** Current data shows 60 days of pure uptrend. Cannot verify guard effectiveness without it.
- **Does MomentumBreakdown SHORT work in real downtrends?** PF=1.50 on 166-229 trades across 3 assets. Promising but needs verification.
- **Should the system default to LONG_ONLY?** Until SHORT is fixed, LONG_ONLY would avoid 0.26 PF. But DirectionController already provides this dynamically.
- **What if real slippage exceeds 0.50%?** At 0.50% PF=1.59. Margin is thin. Volatile events may cause 1%+ slippage.
