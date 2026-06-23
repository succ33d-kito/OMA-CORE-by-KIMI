# OSIRIS Crypto Stability Audit Report
> Generated: 2026-06-23 02:34:19 UTC

## Methodology

Synthetic hourly OHLCV data generated with realistic crypto parameters:
- Base price: $50,000 (BTC), ~$3,125 (ETH)
- Annualized drift: +8%
- Annualized volatility: 60%
- Seed-random for reproducibility

Full pipeline executed per event: MarketAgent → RiskAgent → Council → PaperTradingEngine.

---

## Results Summary

| Duration | Cycles | Trades | Closed | PnL% | MaxDD% | Final Guard | Runtime Err | Exceptions | Guard Fail | Stuck Pos | Time (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 30d | 700 | 32 | 29 | -4.91 | 6.95 | normal | 0 | 0 | 0 | 0 | 16.8 |
| 60d | 1420 | 63 | 60 | -8.85 | 9.55 | caution | 0 | 0 | 0 | 0 | 39.8 |
| 90d | 2140 | 13 | 13 | -3.90 | 3.90 | emergency | 0 | 0 | 0 | 0 | 46.2 |
| 180d | 4300 | 32 | 32 | -7.71 | 8.97 | caution | 0 | 0 | 0 | 0 | 93.0 |

## Verdict

**FAIL** — See individual failures below.

---

## Guard Transition Analysis

### 30d Simulation
- Guard transitions: 3
- Final guard mode: `normal`
- Kill switch activated: False

| From | To | Cycle | Event |
|---|---|---|---|
| normal | caution | 163 | BTC_182 |
| caution | emergency | 237 | BTC_256 |
| emergency | normal | 321 | BTC_340 |

### 60d Simulation
- Guard transitions: 9
- Final guard mode: `caution`
- Kill switch activated: False

| From | To | Cycle | Event |
|---|---|---|---|
| normal | caution | 33 | BTC_52 |
| caution | normal | 35 | BTC_54 |
| normal | caution | 334 | BTC_353 |
| caution | emergency | 336 | BTC_355 |
| emergency | normal | 367 | BTC_386 |
| normal | caution | 635 | BTC_654 |
| caution | emergency | 706 | BTC_725 |
| emergency | normal | 761 | BTC_780 |
| normal | caution | 834 | BTC_853 |

### 90d Simulation
- Guard transitions: 2
- Final guard mode: `emergency`
- Kill switch activated: False

| From | To | Cycle | Event |
|---|---|---|---|
| normal | caution | 33 | BTC_52 |
| caution | emergency | 35 | BTC_54 |

### 180d Simulation
- Guard transitions: 8
- Final guard mode: `caution`
- Kill switch activated: False

| From | To | Cycle | Event |
|---|---|---|---|
| normal | caution | 7 | BTC_26 |
| caution | emergency | 15 | BTC_34 |
| emergency | normal | 51 | BTC_70 |
| normal | emergency | 99 | BTC_118 |
| emergency | normal | 120 | BTC_139 |
| normal | caution | 138 | BTC_157 |
| caution | emergency | 149 | BTC_168 |
| emergency | caution | 162 | BTC_181 |

## Crash Event Analysis

### 30d Simulation
- Warning events: 560
- Emergency events: 88
- Panic events: 0
- Final crash mode: `warning`

| Mode | Score | Cycle | Event |
|---|---|---|---|
| emergency | 45.0 | 8 | BTC_27 |
| emergency | 45.0 | 8 | ETH_27 |
| emergency | 45.0 | 19 | BTC_38 |
| emergency | 45.0 | 19 | ETH_38 |
| emergency | 45.0 | 20 | BTC_39 |

### 60d Simulation
- Warning events: 1300
- Emergency events: 444
- Panic events: 0
- Final crash mode: `warning`

| Mode | Score | Cycle | Event |
|---|---|---|---|
| emergency | 45.0 | 8 | BTC_27 |
| emergency | 45.0 | 8 | ETH_27 |
| emergency | 45.0 | 19 | BTC_38 |
| emergency | 45.0 | 19 | ETH_38 |
| emergency | 45.0 | 20 | BTC_39 |

### 90d Simulation
- Warning events: 2466
- Emergency events: 1074
- Panic events: 0
- Final crash mode: `warning`

| Mode | Score | Cycle | Event |
|---|---|---|---|
| emergency | 45.0 | 8 | BTC_27 |
| emergency | 45.0 | 8 | ETH_27 |
| emergency | 45.0 | 19 | BTC_38 |
| emergency | 45.0 | 19 | ETH_38 |
| emergency | 45.0 | 20 | BTC_39 |

### 180d Simulation
- Warning events: 3226
- Emergency events: 44
- Panic events: 0
- Final crash mode: `none`

| Mode | Score | Cycle | Event |
|---|---|---|---|
| emergency | 50.0 | 8 | BTC_27 |
| emergency | 50.0 | 8 | ETH_27 |
| emergency | 50.0 | 9 | BTC_28 |
| emergency | 50.0 | 9 | ETH_28 |
| emergency | 45.0 | 18 | BTC_37 |

## Direction Controller State

### 30d Simulation
- Allowed directions: `both`
- Long WR: 0.167 | Short WR: 0.2
- Long disabled: True | Short disabled: True

### 60d Simulation
- Allowed directions: `both`
- Long WR: 0.2 | Short WR: 0.2
- Long disabled: True | Short disabled: True

### 90d Simulation
- Allowed directions: `both`
- Long WR: 0.2 | Short WR: 0.125
- Long disabled: True | Short disabled: True

### 180d Simulation
- Allowed directions: `both`
- Long WR: 0.15 | Short WR: 0.0
- Long disabled: True | Short disabled: True

## Open Position Leakage

| 30d | 3 | ⚠️ |
| 60d | 3 | ⚠️ |
| 90d | 0 | ✅ |
| 180d | 0 | ✅ |

## Memory Growth

| 30d | 700 | ~1400KB |
| 60d | 1420 | ~2840KB |
| 90d | 2140 | ~4280KB |
| 180d | 4300 | ~8600KB |
