# OSIRIS Crypto Signal Quality Audit Report
> Generated: 2026-06-23 02:35:43 UTC
> Signals analyzed: 8213

## Methodology

Each signal's recommendation is compared against forward price movement
at 6h, 12h, 24h, 48h, and 72h horizons. Directional accuracy measures
whether the market moved in the predicted direction.

---

## Overall Signal Distribution

| Recommendation | Count | % of Total |
|---|---|---|
| buy | 1731 | 21.1% |
| hedge | 3308 | 40.3% |
| sell | 3174 | 38.6% |

## Directional Accuracy by Horizon

| Horizon | Signals | Correct | Wrong | Accuracy % | Avg Fwd Return % | Median Fwd Return % |
|---|---|---|---|---|---|---|
| 6h | 8213 | 4291 | 3922 | 52.2% | +1.29 | -2.42 |
| 12h | 8213 | 4438 | 3775 | 54.0% | +2.28 | -6.13 |
| 24h | 8213 | 4539 | 3674 | 55.3% | +4.96 | -14.54 |
| 48h | 8213 | 4713 | 3500 | 57.4% | +10.55 | -27.27 |
| 72h | 8213 | 4971 | 3242 | 60.5% | +12.45 | -40.95 |

## Directional Accuracy by Recommendation

| Rec | Count | 6h Acc% | 12h Acc% | 24h Acc% | 48h Acc% | 72h Acc% |
|---|---|---|---|---|---|---|
| buy | 1731 | 47.8% | 45.2% | 39.2% | 31.3% | 30.4% |
| sell | 3174 | 52.3% | 56.0% | 57.9% | 64.2% | 67.9% |
| hedge | 3308 | 54.5% | 56.7% | 61.2% | 64.5% | 69.2% |

## Outcome by Asset

### BTC
| Horizon | Signals | Accuracy % | Avg Return % |
|---|---|---|---|
| 6h | 4120 | 50.8% | +1.55 |
| 12h | 4120 | 52.1% | +2.62 |
| 24h | 4120 | 52.7% | +6.50 |
| 48h | 4120 | 56.5% | +15.62 |
| 72h | 4120 | 59.9% | +16.83 |

### ETH
| Horizon | Signals | Accuracy % | Avg Return % |
|---|---|---|---|
| 6h | 4093 | 53.7% | +1.03 |
| 12h | 4093 | 56.0% | +1.94 |
| 24h | 4093 | 57.9% | +3.41 |
| 48h | 4093 | 58.3% | +5.44 |
| 72h | 4093 | 61.2% | +8.04 |

## Conviction vs Outcome

| Conviction | Count | 24h Acc% | 24h Avg Ret% |
|---|---|---|---|
| 40-60 | 4052 | 57.5% | +5.01 |
| 60-80 | 54 | 50.0% | -11.62 |
| 80-101 | 4107 | 53.2% | +5.13 |

## Consensus Score vs Outcome

| Consensus | Count | 24h Acc% | 24h Avg Ret% |
|---|---|---|---|

## Best/Worst Signals

### 24h Forward
- Best: BTC_3520 — +876.35% (hedge @ 50 conf)
- Worst: BTC_3276 — -89.27% (hedge @ 50 conf)

### 72h Forward
- Best: BTC_3494 — +1662.26% (sell @ 90 conf)
- Worst: BTC_349 — -97.48% (buy @ 90 conf)

## False Positive / Negative Analysis

| Metric | Count |
|---|---|
| False Positive BUY (predicted up, fell >2%) | 1040 |
| False Negative BUY (missed up move >2%) | 659 |
| False Positive SELL (predicted down, rose >2%) | 2531 |
| False Negative SELL (missed down move >2%) | 3797 |

## Summary

- Total actionable signals: 8213
- 24h directional accuracy: 55.3%
- 24h average forward return: +4.96%
