# OSIRIS Survival Stress Audit Report
> Generated: 2026-06-23 02:42:43 UTC

## Methodology
Hostile regimes are replayed through the full OSIRIS pipeline.
Each regime uses synthetic OHLCV calibrated to match historical crisis characteristics.
Protection layers (CrashDetector, CapitalGuard, KnifeDetector, etc.) are monitored.

---

## Results Matrix

| Regime | Cycles | Trades | PnL% | MaxDD% | Final Guard | Guard Δ | Crash W | Crash E | Crash P | Final Crash | Direction | Blocks | Survived |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| COVID Crash 2020 | 4280 | 66 | +41.77 | 2.88 | emergency | 7 | 610 | 23 | 0 | none | both | 3829 | ✅ |
| Luna/3AC Crash | 2840 | 59 | +37.55 | 4.25 | caution | 7 | 403 | 14 | 0 | none | both | 2015 | ✅ |
| FTX Collapse | 2120 | 56 | +36.69 | 4.47 | emergency | 9 | 281 | 1 | 0 | none | both | 1640 | ✅ |
| Strong Bull Trend | 2840 | 223 | +107.18 | 3.97 | normal | 22 | 9 | 0 | 0 | none | long_only | 1833 | ✅ |
| Sideways Chop | 2840 | 117 | +12.95 | 6.45 | normal | 16 | 0 | 0 | 0 | none | both | 1321 | ✅ |
| Flash Crash Synthetic | 440 | 5 | +2.89 | 1.11 | normal | 0 | 5 | 1 | 0 | none | long_only | 429 | ✅ |

## Per-Regime Analysis

### COVID Crash 2020
- **Cycles**: 4280
- **PnL**: +41.77% | **Max DD**: 2.88%
- **Guard**: Final = `emergency`, transitions = 7
- **CrashDetector**: Warnings 610, Emergencies 23, Panics 0
- **Capital survived**: ✅ $14176.81
- **Kill switch**: ✅ Not activated
- **Direction**: both

### Luna/3AC Crash
- **Cycles**: 2840
- **PnL**: +37.55% | **Max DD**: 4.25%
- **Guard**: Final = `caution`, transitions = 7
- **CrashDetector**: Warnings 403, Emergencies 14, Panics 0
- **Capital survived**: ✅ $13755.07
- **Kill switch**: ✅ Not activated
- **Direction**: both

### FTX Collapse
- **Cycles**: 2120
- **PnL**: +36.69% | **Max DD**: 4.47%
- **Guard**: Final = `emergency`, transitions = 9
- **CrashDetector**: Warnings 281, Emergencies 1, Panics 0
- **Capital survived**: ✅ $13668.71
- **Kill switch**: ✅ Not activated
- **Direction**: both

### Strong Bull Trend
- **Cycles**: 2840
- **PnL**: +107.18% | **Max DD**: 3.97%
- **Guard**: Final = `normal`, transitions = 22
- **CrashDetector**: Warnings 9, Emergencies 0, Panics 0
- **Capital survived**: ✅ $20718.08
- **Kill switch**: ✅ Not activated
- **Direction**: long_only

### Sideways Chop
- **Cycles**: 2840
- **PnL**: +12.95% | **Max DD**: 6.45%
- **Guard**: Final = `normal`, transitions = 16
- **CrashDetector**: Warnings 0, Emergencies 0, Panics 0
- **Capital survived**: ✅ $11294.80
- **Kill switch**: ✅ Not activated
- **Direction**: both

### Flash Crash Synthetic
- **Cycles**: 440
- **PnL**: +2.89% | **Max DD**: 1.11%
- **Guard**: Final = `normal`, transitions = 0
- **CrashDetector**: Warnings 5, Emergencies 1, Panics 0
- **Capital survived**: ✅ $10289.38
- **Kill switch**: ✅ Not activated
- **Direction**: long_only

## Key Questions

**COVID-style crash detected as WARNING+?**
✅ YES — 610 warnings, 23 emergencies

**COVID Crash 2020: Loss capped and guards working?**
✅ Survived with +41.77% PnL, max DD 2.88%

**Luna/3AC Crash: Loss capped and guards working?**
✅ Survived with +37.55% PnL, max DD 4.25%

**FTX Collapse: Loss capped and guards working?**
✅ Survived with +36.69% PnL, max DD 4.47%

**Strong Bull Trend: Loss capped and guards working?**
✅ Survived with +107.18% PnL, max DD 3.97%

**Sideways Chop: Loss capped and guards working?**
✅ Survived with +12.95% PnL, max DD 6.45%

**Flash Crash Synthetic: Loss capped and guards working?**
✅ Survived with +2.89% PnL, max DD 1.11%

**CrashDetector activates early enough?**
✅ All crashes detected at WARNING+ level

**CapitalGuard prevents deadlock?**
✅ No guard deadlock (no regime ended in HALT)
