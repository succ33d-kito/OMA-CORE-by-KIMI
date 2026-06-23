# MarketAgent Signal Flow Audit — FLAW-14 Analysis

> Generated: 2026-06-23  
> File: `core/agents/market_agent.py` (lines 91-126)

---

## Current If/Elif Chain (Lines 91-126)

```
Priority 1: uptrend + momentum>0 + RSI<70       → BUY       [line 91]
Priority 2: downtrend + momentum<0 + RSI>30      → SELL      [line 95]
Priority 3: RSI>70 + short_style rsi/combined    → SELL      [line 99]
Priority 4: close<5-period-low + mom_break        → SELL      [line 104]
Priority 5: RSI<30                                → BUY       [line 109]
Priority 6: volatility > 5%                       → HEDGE     [line 114]
Priority 7: momentum_strength > 1%                → BUY/SELL  [line 118]
else:                                              → WATCH     [line 125]
```

## FLAW-14: MomBreak SHORT Blocks RSI<30 BUY

**Bug**: Condition 4 (MomBreak SHORT, line 104) is evaluated **before** condition 5 (RSI oversold BUY, line 109).

**Scenario**:
- Price breaks below its 5-period low → condition 4 matches → SELL signal
- RSI is simultaneously below 30 (oversold) → condition 5 would match BUY
- But condition 4 already matched in the elif chain → condition 5 is **never evaluated**
- Result: SELL when the system should be considering BUY

**Root cause**: The elif chain creates a hidden priority hierarchy where `mom_break` (a short-term momentum pattern) overrides `rsi_oversold` (a mean-reversion pattern) regardless of signal strength.

## All Conditions Analyzed

### LONG Conditions

| Condition | Line | Triggers | Score Basis |
|---|---|---|---|
| Uptrend BUY | 91 | trend=uptrend, momentum>0, RSI<70 | 0.6 + trend_strength*2 |
| RSI oversold BUY | 109 | RSI<30 | 0.5 + (30-RSI)/60 |
| Momentum BUY | 118 | momentum_strength>1, momentum>0 | (no impact_score change) |

### SHORT Conditions

| Condition | Line | Triggers | Score Basis |
|---|---|---|---|
| Downtrend SELL | 95 | trend=downtrend, momentum<0, RSI>30 | 0.6 + trend_strength*2 |
| RSI overbought SELL | 99 | RSI>70, short_style rsi/combined | 0.5 + (RSI-70)/60 |
| MomBreak SELL | 104 | close<5p-low, short_style mom_break/combined | 0.5 + trend_strength*2 |
| Momentum SELL | 118 | momentum_strength>1, momentum<0 | (no impact_score change) |

### Other Conditions

| Condition | Line | Triggers |
|---|---|---|
| High volatility HEDGE | 114 | volatility > 0.05 |
| WATCH (default) | 125 | No condition matches |

## Condition Order Bugs

1. **FLAW-14**: MomBreak SHORT (line 104) blocks RSI<30 BUY (line 109)
2. **Minor**: Momentum BUY/SELL (line 118) is blocked by HEDGE (line 114) — if volatility > 5%, momentum signals are suppressed entirely even if the momentum is very strong (this may be intentional)
3. **Minor**: Uptrend BUY (line 91) blocks overbought SELL (line 99) and MomBreak SHORT (line 104) when uptrend is present — correct behavior since uptrend takes priority

## Signal Mode and Short Style Interaction

| Parameter | Behavior |
|---|---|
| `signal_mode = "both"` | All signals pass through |
| `signal_mode = "long_only"` | Blocks SELL signals after selection (lines 131-133) |
| `signal_mode = "short_only"` | Blocks BUY signals after selection (lines 128-130) |
| `short_style = "mom_break"` | Enables line 104 (MomBreak SELL) |
| `short_style = "rsi"` | Enables line 99 (RSI overbought SELL) |
| `short_style = "combined"` | Enables both RSI and MomBreak SELL |
| `signal_mode` | Applied AFTER signal selection — not affected by FLAW-14 |

## Fix Strategy

Replace the if/elif chain with a candidate-based signal selection:

1. Evaluate all LONG conditions → produce scored LONG candidates
2. Evaluate all SHORT conditions → produce scored SHORT candidates
3. Select the highest-scoring candidate overall
4. If no candidate meets threshold → fall back to HEDGE (if volatile) or WATCH
5. Apply `signal_mode` filter after selection (same as current)
6. Preserve all existing `impact_score` and `risk_score` formulas per condition
