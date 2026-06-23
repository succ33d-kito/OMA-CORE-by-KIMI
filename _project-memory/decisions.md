# Architectural Decisions — OSIRIS / O.M.A.-C.O.R.E.

## ADR-001: Hybrid Event-Driven Architecture

**Status**: Accepted (2026-06-21)
**Context**: The existing pipeline (Collectors → DB → Scoring → Opportunities) worked but tightly coupled components. The OSIRIS vision requires an event-driven agent system.
**Decision**: Keep the existing pipeline as-is. Add an EventBus layer alongside it. Collectors publish to EventBus. Agents subscribe as processors. The Council reads from the bus and publishes decisions. The Opportunity Engine still reads from DB.
**Consequence**: No rewrite of working code. Gradual migration. New components are decoupled. Single-person-manageable complexity.
**Revisit if**: System needs multi-process scaling → replace in-memory EventBus with Redis.

## ADR-002: Structured Agent Communication (ACP)

**Status**: Accepted (2026-06-21)
**Context**: Agents need to communicate decisions to the Council and downstream components. Free text is not machine-readable, not comparable, and not aggregatable.
**Decision**: All agents communicate via `AgentOpinion` (agent_name, confidence, impact_score, risk_score, evidence, recommendation, rationale). The Council produces `CouncilDecision` (conviction, consensus_score, disagreement_score, action).
**Consequence**: Every agent output is parseable, comparable, and aggregatable. Council decisions are transparent (you can see which agents agreed/disagreed and why).
**Revisit if**: New fields are consistently needed — add to the dataclass, don't overload `metadata`.

## ADR-003: WorldMonitorV2 Replaces WorldMonitor

**Status**: Accepted (2026-06-21)
**Context**: The original `WorldMonitor` class in `world_monitor.py` only instantiated `CoinGeckoCollector`, ignoring the other 7 collectors. The CLI's `collect` command was broken — it only collected crypto data.
**Decision**: Created `WorldMonitorV2` in a new file (`world_monitor_v2.py`) that instantiates ALL collectors and publishes each event to the EventBus. Marked original as deprecated with `DeprecationWarning`.
**Consequence**: CLI now collects from all 7 sources. Events flow through the EventBus automatically. Old code still works for backward compatibility.
**Revisit if**: WorldMonitorV2 is proven stable → remove deprecated `world_monitor.py`.

## ADR-004: Non-Destructive PostgreSQL Migration

**Status**: Accepted (2026-06-21)
**Context**: `migrate_to_postgres.py` used `DROP TABLE ... CASCADE` before recreating tables. Each run destroyed all existing data.
**Decision**: Changed to `CREATE TABLE IF NOT EXISTS` + `INSERT ... ON CONFLICT DO UPDATE`. No data loss on re-run.
**Consequence**: Safe to run on any schedule. Existing rows are updated, new rows inserted, nothing deleted.
**Revisit if**: Schema changes require column additions/removals — handle migrations with ALTER TABLE.

## ADR-005: Rule-Based Agents (No LLM Yet)

**Status**: Accepted (2026-06-21)
**Context**: LLM calls add latency, cost, and API dependency. The codebase has no AI dependencies.
**Decision**: NewsAgent and MacroAgent are rule-based with keyword scoring, sentiment analysis, and indicator matching. They produce properly structured `AgentOpinion` objects with confidence scores.
**Consequence**: Zero external dependencies, fast execution, deterministic output. Less nuanced than LLM-based analysis but fully functional and testable.
**Revisit if**: News classification quality becomes a bottleneck. The ACP schema is designed to work with LLM-produced opinions — just swap the agent internals.

## ADR-006: Three-Profile Model (Trader, Entrepreneur, Creator)

**Status**: Accepted (2026-06-21)
**Context**: The OSIRIS bible defines three user profiles. The existing code had an empty `user_profiles` table with no logic.
**Decision**: Created typed preference classes (`TraderPreferences`, `EntrepreneurPreferences`, `CreatorPreferences`) with sensible defaults. `ProfileRegistry` handles CRUD + DB persistence. `MetaCouncil` evaluates opportunities across all three profiles.
**Consequence**: Every opportunity can be scored for trading, business, and content value. Users can switch profiles. New profile types can be added by subclassing.
**Revisit if**: Profiles need dynamic fields not captured by dataclasses — consider JSON schema-based preferences.

## ADR-007: Memory as Service, Not Database

**Status**: Accepted (2026-06-21)
**Context**: The OSIRIS bible mentions short-term memory, long-term memory, RAG, Vector DB, and Knowledge Graph.
**Decision**: Start with `ShortTermMemory` (TTL-expiring dict), `LongTermMemory` (tag-indexed dict), and `MemoryStore` (event-keyed opinion cache). These are in-memory Python classes, not persistent databases.
**Consequence**: Zero infrastructure. Works immediately. Vector DB (ChromaDB) and Knowledge Graph (NetworkX) can be added as new implementations behind the same `MemoryStore` interface.
**Revisit if**: Memory persistence across restarts is needed → add SQLite backend or Redis. For semantic search → add ChromaDB integration.

## ADR-008: Agent Council Calculates Weighted Consensus

**Status**: Accepted (2026-06-21)
**Context**: Multiple agents produce opinions on the same event. The Council needs to aggregate them into a single decision with a measure of agreement/disagreement.
**Decision**: The Council calculates:
- `consensus_score = max(0, 100 - stdev(confidences) * 20)` — lower variance = higher consensus
- `disagreement_score = stdev(confidences) * 20` — standard deviation scaled to 0-100
- `conviction = avg_impact * 30 + weighted_confidence * 40 + avg_risk * 10 + consensus_score * 20` — weighted components
- Action is chosen by majority vote across recommendations
- Evidence from multiple agents is cross-referenced and the most-cited evidence is surfaced in the rationale
**Consequence**: Decisions are transparent and explainable. You can see exactly why conviction is high or low, which agents agreed, and what evidence drove the decision.
**Revisit if**: Agents become LLM-powered and need more nuanced consensus (e.g., Borda count or ranked-choice voting).

## ADR-009: Project Memory as Handoff Protocol

**Status**: Accepted (2026-06-21)
**Context**: AI sessions have no persistent memory. Each new session starts from scratch. Critical context is lost between handoffs.
**Decision**: Maintain four files in `_project-memory/` as the single source of truth:
- `README.md` — permanent project identity (rarely changes)
- `STATUS.md` — live inventory of what works and what's next (updated every session)
- `progress.md` — chronological log of changes (appended to, never rewritten)
- `decisions.md` — ADRs with rationale, consequences, and revisit conditions (appended to, existing entries never modified)
**Consequence**: Any AI starting a new session can rebuild full context from these files + a quick test run. No tribal knowledge. No repeated work.
**Revisit if**: The project grows large enough to warrant a wiki or a docs site — but keep these files as the canonical source.

## ADR-010: Rule-Based Trading Pipeline (Council → Performance)

**Status**: Accepted (2026-06-21, session 2)
**Context**: Council decisions produce opinions and metadata, but nothing acted on them. The gap between "the council thinks" and "real money trades" was wide. Multiple approaches were possible: LLM trading agent, full backtester with broker API, or an iterative pipeline.
**Decision**: Build a 4-stage pipeline between Council and execution:
1. `TradeSignal` schema — structured bridge (event_id, council_decision_id, direction, entry, SL, TP, position_size_pct)
2. `MarketAgent` + `RiskAgent` — rule-based trading-specific agents that produce agent opinions consumed by the Council
3. `BacktestEngineV2` — real OHLCV via Binance/yfinance, candle-by-candle SL/TP simulation
4. `PaperTradingEngine` — stateful position management with conviction→size mapping, feeds `PerformanceMemory`
`PerformanceMemory` closes the loop: agents with good track records get higher weight in future Council decisions (via EMA α=0.1).
**Consequence**: Full trading pipeline without external dependencies. All components testable with mock or real data. PerformanceMemory enables the Council to learn from trading outcomes. No slippage model yet — entry is open of first candle after signal (optimistic).
**Revisit if**: Paper trading proves the pipeline works and real broker API integration is needed. Add execution agent behind the same TradeSignal interface.

## ADR-011: Validation Sprint — Evidence-Based Pivot Required

**Status**: Findings (2026-06-22, session 3)
**Context**: The entire trading pipeline was built (sessions 1-2) but never tested with real data. Session 3 ran a full validation sprint: system audit, end-to-end integration tests, 14-day paper trading experiment on real Binance data (BTC/ETH/SOL, 1,365 events, 292 trades), agent attribution, council validation, and production readiness assessment.
**Findings**:
1. **Conviction formula has predictive value** (r ≈ +0.036, 1,293 samples). High conviction avg outcome -0.11% vs low conviction -0.85%. Delta = +0.74%. The Council math is directionally correct.
2. **RiskAgent fixed confidence=0.75 is fatal**. MarketAgent's variable ~0.62 confidence is consistently outvoted. RiskAgent always recommends BUY when volatility is normal. Result: **100% of 292 trades are LONG**. No short trades in 14 days. The system systematically loses money in any downward or volatile period.
3. **2-agent consensus is meaningless**: stdev of 2 confidence values is always small → consensus_score ≈ 98/100 always. Zero discriminatory power. Adding a third agent is the minimum fix.
4. **ATR × 1.5 stops are too tight for crypto**: 92% of trades (270/292) hit stop loss before take profit. Crypto needs ×2.5-3.0.
5. **Track record effect is too weak**: ±10% modifier range. An agent with 90% accuracy adds only 2% more conviction vs one with 50%.
6. **Both agents severely overconfident**: market bias +0.545, risk bias +0.675 (confidence is 3-4× actual accuracy).
7. **PerformanceMemory is in-memory only**: all learning resets every session.
**Consequence**: The system can predict direction (conviction works) but cannot execute profitably. Paper trading lost -123% over 14 days. Production readiness: Paper Trading 60%, Demo 30%, Real Capital 0%.
**Action Required**: Fix FLAW-1 (RiskAgent dynamic confidence), FLAW-2 (add 3rd agent), FLAW-3 (widen stops) before building any new features. Validation before expansion.

## ADR-012: Recovery Sprint — WATCH Veto + Both Directions + ATR×3.0

**Status**: Accepted (2026-06-22, session 4)
**Context**: Validation sprint (ADR-011) found -123% return with 100% LONG bias. Root cause: RiskAgent fixed confidence=0.75 with BUY default dominated Council votes. Needed to unlock SHORT trades, add vote diversity, and fix stop sizing.
**Changes Made**:
1. **RiskAgent → WATCH default**: Confidence now dynamic (0.30-0.85) based on data quality, event clarity, and market stress. Default recommendation changed from BUY to WATCH. RiskAgent is veto-only (produces AVOID/HEDGE/WATCH, never initiates direction).
2. **Council WATCH-ignore**: When at least one agent recommends BUY/SELL, the Council ignores WATCH/HOLD/NO_ACTION votes for the action selection. This prevents high-confidence WATCH votes from blocking low-confidence directional signals.
3. **3rd agent (TrendAgent) built but not used**: EMA-based trend follower (6-direction alignment). Tested, adds noise in every configuration tested. 2-agent (market+risk) outperforms 3-agent in all experiments.
4. **ATR×3.0 optimal**: Widest stop tested. Both stop and take_profit scale with ATR multiplier at 2:1 fixed ratio. ATR×1.5 and ATR×2.0 were too tight.
5. **Signal mode filtering**: MarketAgent supports `signal_mode` = both / short_only / long_only. SHORT-only achieves 89.2% WR in choppy 14-day window. BOTH directions achieves 61.9% WR over 60 days.
**Results**:
| Metric | Before (Baseline) | After (ATR×3.0, 60d) |
|--------|-------------------|----------------------|
| Win rate | 7.5% | 61.9% |
| Return | -123.00% | +514.63% |
| Sharpe | -23.18 | 7.68 |
| Equity | $0 (bankrupt) | $61,463.09 |
| LONG/SHORT ratio | 100/0 | 67/33 |
**Key Findings**:
- **LONG trend-following on BTC/ETH**: 83.9% WR over 60 days (SMA20 > SMA50, RSI < 70, momentum > 0)
- **SHORT mean reversion on SOL**: 89.2% WR in choppy 14-day window (RSI > 70)
- **Regime dependency**: SHORT wins in range-bound, LONG wins in sustained uptrend. No regime detection exists.
- **TrendAgent adds noise**: 3-agent results are worse than 2-agent in every test
**Revisit if**:
- TrendAgent is improved with proper entry timing (not just EMA cross alignment)
- Regime detection is added to switch between LONG-heavy and SHORT-heavy weighting
- LONG signals are improved to reduce the 28% WR on BTC/ETH LONG trades
- PerformanceMemory persistence makes track records meaningful across sessions

## ADR-013: Research Sprint — Capital Tracking Fix + Findings

**Status**: Accepted (2026-06-22, session 5)
**Context**: Recovery sprint (ADR-012) claimed +514% over 60 days. Research sprint was tasked with validating whether this alpha is real, robust, and transferable. Rules: no new agents, no new indicators, no new infrastructure. Research first, expansion later.
**Critical Bug Found During Research**:
- **Position sizing always used initial capital** (`self.capital` set once in `__init__` and never updated with P&L). All trades were sized as a percentage of the initial $10,000 regardless of current equity. This caused:
  - Under-compounding in winning streaks (positions stayed small even as equity grew)
  - Over-risking in losing streaks (positions stayed large even as equity shrank)
  - Negative equity possible (equity went to -$5,899 in one 30-day run)
- **Fix**: Added `self.closed_pnl` tracking in `_record_trade_result`. `self.capital` now updates to `initial_capital + closed_pnl` after every trade. Position sizing uses actual current equity.
**Impact of Fix**: 30-day return corrected from +110% to +37.9%. 60/90-day returns remain high but are now due to genuine compounding (not a bug). All previous absolute return figures from recovery sprint are overstated.
**Phase-by-Phase Findings**:
1. **Robustness**: Alpha persists across 30/60/90 days. 30d (+37.9%) is the most reliable estimate. 60/90d returns are inflated by geometric compounding in an ideal backtest.
2. **Regime Analysis**: Alpha is regime-dependent. LONG trend-following (SMA20/50, RSI<70) wins 78% in uptrends. SHORT mean-reversion (RSI>70) loses 78% in uptrends (0.26 profit factor).
3. **LONG/SHORT Attribution**: LONG produces all alpha (PF=11.02). SHORT destroys it (PF=0.26). The system is profitable only because LONG wins outweigh SHORT losses.
4. **Conviction Validation**: Conviction predicts DIRECTION but not quality within direction. Top 10% conviction = 92.6% WR in mixed-direction regime. In single-direction (100% LONG) regime, conviction inverts (r=-0.465).
5. **Agent Attribution**: MarketAgent = alpha generator. RiskAgent = veto gatekeeper. Neither works alone. Minimum viable = both.
6. **Regime Detection Design**: Proposed two-level adaptive bias (rolling 20-trade WR per direction) over full RegimeAgent. SHORT should be disabled or reduced when WR < 25%.
**New Flaws Discovered**:
- **[FLAW-7] Capital tracking bug**: All previous return figures overstated. FIXED.
- **[FLAW-8] SHORT systematically loses**: 22% WR in uptrends. Counter-trend RSI>70 signal is the cause.
- **[FLAW-9] No slippage model**: Paper returns dramatically inflated by compounding (10k → 38B in 60d). Not realistic.
- **[FLAW-10] Conviction no single-direction power**: Works across directions but not within same direction.
**Research Report**: `_project-memory/research_report.md`
**Conclusion**: Alpha IS real (per-trade expectancy positive, WR directionally consistent). Alpha is NOT robust in magnitude (compounding exaggerates returns). Alpha is NOT fully transferable (SHORT fails in uptrends). Before live capital: add slippage model, adaptive direction bias, and fix SHORT signal.

## ADR-014: Alpha Realism Sprint — SlippageEngine + DirectionController + CapitalGuard

**Status**: Accepted (2026-06-22)
**Context**: Research sprint (ADR-013) confirmed alpha is real but identified three critical gaps: no slippage model (FLAW-9), SHORT systematically loses (FLAW-8), and no capital protection. The next step is transforming simulated alpha into realistic, cost-adjusted, capital-protected alpha.
**Decision**: Build three utility modules (not agents) to address each gap:
1. **SlippageEngine** (`core/execution/slippage.py`): Configurable slippage + per-asset spread (BTC=1bps, ETH=2bps, SOL=3bps). Affects entry, exit, stop, and target prices. No new infrastructure.
2. **DirectionController** (`core/execution/direction_controller.py`): Rolling 20-trade WR per direction. Disables LONG or SHORT when WR < 25% over last 20 trades. Implements the two-level adaptive bias proposed in Phase 6 of research sprint.
3. **CapitalGuard** (`core/execution/capital_guard.py`): Max daily loss 10%, max weekly loss 20%, max open risk 25%, kill switch. Position sizing reduces when thresholds approach.

**Consequence**: 
- Positive: All three modules integrate cleanly into existing PaperTradingEngine. No new agents. No infrastructure. 91 existing tests pass unchanged.
- Negative: DirectionController cannot be verified in bearish conditions (current 60d window is 100% LONG, 98.5% WR). CapitalGuard untriggered in favorable window.
- Position sizing fix: `self.capital` → `self._risk_base()` (grows 0.1%/trade). Prevents unrealistic compounding ($10k → $16M → now $88k for same 30d window).
- SHORT root cause found: RSI>70 mean reversion (PF=0.04) should be replaced with MomentumBreakdown (PF=1.50). Not yet implemented in MarketAgent.

**Revisit if**: Bearish window appears → re-run Phase 8 with all guards. Need to verify guard effectiveness before demo capital deployment.

## ADR-015: Position Sizing Uses risk_base (Not Current Equity)

**Status**: Accepted (2026-06-22)
**Context**: PaperTradingEngine positioned trades using `self.capital` (total equity). In high-frequency mode (736 trades in 30d), this causes absurd compounding: $10k → $16M. Real-world HF traders don't compound their full capital every trade.
**Decision**: Replace `self.capital` with `self._risk_base()` for position sizing. `_risk_base()` = `min(self.capital, initial_capital * (1 + total_trades * 0.001))`. Grows by at most 0.1% per trade from initial capital.
**Consequence**: 
- After 736 trades: max base = $17,360 (vs $88,376 actual equity)
- 30d return corrected: +31,583% → +783.76% (still high due to 97.8% WR regime artifact)
- Realistic for paper trading; prevents runaway sizing in favorable markets
- Does NOT affect performance metrics (WR, PF, Sharpe) — those are independent of position size
- Only affects absolute return magnitude (which was meaningless without realistic sizing)
**Revisit if**: Adding Kelly criterion or fixed-fraction sizing → replace `_risk_base()` with the new model.

## ADR-016: SHORT Signal Requires Replacement, Not Optimization

**Status**: Pending implementation (2026-06-22)
**Context**: Research sprint (ADR-013) showed SHORT has PF=0.26. Phase 4 of alpha realism sprint diagnosed the root cause: RSI>70 mean reversion has PF=0.04 (ETH) to 0.40 (BTC). MomentumBreakdown (close < lowest of last 5 candles) has PF=1.23-1.50 and 42.9% WR. EMACrossDown has PF=3.00 (but only 3-5 signals).
**Decision**: Replace RSI>70 SHORT signal in MarketAgent with MomentumBreakdown or a combination. The RSI>70 condition fights the trend in uptrends. MomentumBreakdown follows the trend (breakdown after trend exhaustion).
**Consequence**:
- Expected: SHORT PF improves from 0.26 to ~1.40
- Risk: MomentumBreakdown may generate fewer signals in trending markets (only 91-229 trades vs 146-421 for MA SHORT baseline)
- Risk: EMACrossDown has best PF (3.00) but too few signals (3-5) to rely on alone
**Suggested approach**: Combined SHORT signal: MomentumBreakdown OR EMACrossDown (whichever triggers first). If neither, no SHORT.
**Not implemented yet**: Requires code change in `core/agents/market_agent.py`.

## ADR-017: MarketAgent SHORT uses Configurable `short_style` Parameter

**Status**: Accepted (2026-06-22)
**Context**: Phase 4 of Regime Robustness Sprint tested RSI>70 vs MomentumBreakdown SHORT across 6 historical periods. Results show they produce identical results in 4/6 periods because Path A (structure-based SHORT) dominates. The `elif` chain structure means MomBreak blocks RSI<30 BUY signals in ranging markets.
**Decision**: Add `short_style` parameter to MarketAgent with three options:
- "rsi" — original RSI>70 overbought SHORT (Path B)
- "mom_break" — momentum breakdown SHORT (default, from Phase 4 analysis)
- "combined" — RSI>70 OR momentum breakdown (recommended for maximum frequency)

Default is "mom_break" for backward compatibility with Alpha Realism Sprint results.
**Consequence**: 
- Positive: A/B testing now possible without code changes
- Negative: `elif` chain still causes MomBreak to block RSI<30. Need to restructure into independent checks in future session.
- The "combined" style is recommended for demo deployment (captures both overbought and breakdown signals).

## ADR-018: DirectionController Needs Global WR Tracking (Not Rolling Window)

**Status**: Pending implementation (2026-06-22)
**Context**: Phase 5 tested LONG_ONLY/SHORT_ONLY/BOTH across all regimes. SHORT_ONLY loses everywhere (-1.88% to -14.37%). LONG_ONLY ≈ BOTH in most periods because the system generates ~0 SHORT trades in bear markets. The rolling 20-trade window never fills for SHORT because SHORT trades are too rare.
**Decision**: Replace rolling 20-trade window with global WR tracking + minimum trade threshold:
- Global SHORT WR: track lifetime SHORT WR
- Minimum trades: only evaluate after 10+ SHORT trades
- SHORT disabled if global WR < 30%
- Re-enabled when global WR > 40% with 10+ recent SHORT trades
**Consequence**:
- Narrower disabling window (fewer edge cases of SHORT being falsely enabled)
- Less responsive to regime changes (global WR lags)
- Trade-off: reliability over responsiveness

## ADR-019: Demo Capital Readiness — Conditional YES

**Status**: Accepted (2026-06-22)
**Context**: Regime Robustness Sprint shows system survives 87.5% of historical periods (7/8) across 3 regimes. Only failure: COVID-style gap-down crash. Phase 7 computed: 87.5% profitability probability, 95% break-even probability, 12.5% failure probability.
**Decision**: Upgrade demo readiness from NO to CONDITIONAL YES. Conditions:
1. Tighten CapitalGuard max_daily_loss_pct to 5% (from 10%) — catches gap-down early
2. Add manual gap-down trigger: if BTC drops >10% in 24h, operator activates kill switch
3. Accept 12.5% gap-down risk as irreducible
4. Paper trading for minimum 7 days before demo capital activation
**Consequence**:
- 87.5% probability of profitability across regimes
- 12.5% probability of loss (gap-down scenario)
- Gap-down loss limited to ~5% by tighter CapitalGuard
- Total capital at risk in gap-down: ~5% (single day's loss limit)

## ADR-019b: Demo Readiness — Revisión (Session 8)

**Status**: Updated (2026-06-22)
**Context**: Extended Paper Trading & Demo Gate Sprint tested all guards and COVID replay. Found 3 critical blockers:
1. CrashDetector fails multi-day crash detection (FLAW-16)
2. KnifeDetector untested (no LONG signals) (FLAW-17)
3. Kill switch untested (35% DD never reached) (FLAW-18)
**Decision**: Demo readiness downgraded from CONDITIONAL YES to CONDITIONAL (3 blockers remain). Conditions for activation unchanged but must now also include fixes for FLAW-16, FLAW-17, and FLAW-18.
**Consequence**:
- Demo activation postponed until CrashDetector multi-window fix complete
- KnifeDetector verified through forced LONG signal test
- Kill switch verified through controlled drawdown test
- Paper trading remains GO
- Real capital remains NO

## ADR-020: BTC-Only Crash/Gap Detection

**Status**: Accepted (2026-06-22)
**Context**: CrashDetector and GapRiskEngine were receiving price data from multiple assets (BTC, ETH, SOL), causing absurd gap calculations (avg gap 29,409%) and false crash detection (score 70+). Crypto crashes are correlated across assets — BTC serves as market-wide risk proxy.
**Decision**: CrashDetector and GapRiskEngine track BTC prices only. ETH and SOL price events do not update market-wide risk detectors. Per-asset crash detection is not needed when crashes are correlated.
**Consequence**:
- Crash/gap scores now reflect BTC market conditions only
- GapRiskEngine avg gap 0.80% (reasonable, was 29,409%)
- CrashDetector score 10-15 (normal market, was 70+ panic)
- GapRiskEngine max gap 5.26% (captures real BTC gaps)
- Loss of per-asset crash detection (acceptable — no crypto asset crashes independently)

## ADR-021: Guard Activation Logging

**Status**: Accepted (2026-06-22)
**Context**: Phases 1-2 require tracking every guard activation with reason, asset, timestamp, direction, would-be size, and market condition. Existing `process_decision` returns None for blocks but provides no audit trail.
**Decision**: External GuardLogger class captures guard state at decision time. Logs every blocked trade before and after `process_decision`. Separate counters for each guard type.
**Consequence**:
- Complete audit trail of all guard activations
- Can reconstruct: "why was this trade blocked?"
- Requires external wrapper (not in engine itself) — may miss some edge cases
- Future: integrate GuardLogger into PaperTradingEngine

## ADR-022: Gap Risk Cushion on Stop Loss

**Status**: Accepted (2026-06-22)
**Context**: During high gap risk periods (weekends, elevated volatility), stop losses are vulnerable to being gapped through. COVID replay showed 5/5 SHORT stops hit. GapRiskEngine provides stop_cushion_multiplier() that increases stop width based on gap risk score.
**Decision**: PaperTradingEngine.process_decision applies gap_risk.stop_cushion_multiplier() to stop_pct before computing SL/TP. When gap risk is high, stops are wider to avoid gap-through.
**Consequence**:
- Stop width increases by 1.0-1.5x during elevated gap risk
- Wider stops = larger potential losses per trade
- Tradeoff: survive gap-through vs accept larger stop distances
- Only activates when gap risk score > 20 (normal market: no adjustment)
