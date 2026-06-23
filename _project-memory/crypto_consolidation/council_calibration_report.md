# OSIRIS Council Calibration Audit Report
> Generated: 2026-06-23 02:38:34 UTC
> Trades analyzed: 80

## Methodology
Trades are bucketed by conviction, consensus score, disagreement score, and direction.
For each bucket we measure: win rate, average PnL, profit factor, and forward return.

---

## Conviction Bucket Analysis

| Conviction | Count | Win Rate | Avg PnL% | Median PnL% | Profit Factor |
|---|---|---|---|---|---|
| 40-60 | 55 | 63.6% | +1.27 | +8.38 | 1.08 |
| 80-101 | 25 | 56.0% | +10.78 | +21.33 | 1.62 |

## Consensus Score Bucket Analysis

| Consensus | Count | Win Rate | Avg PnL% | Profit Factor |
|---|---|---|---|---|

## Disagreement Score Bucket Analysis

| Disagreement | Count | Win Rate | Avg PnL% | Profit Factor |
|---|---|---|---|---|
| 0-0.1 | 2 | 100.0% | +55.53 | 11106.00 |
| 0.1-0.2 | 6 | 33.3% | -12.00 | 0.67 |
| 0.2-0.3 | 4 | 25.0% | +6.59 | 1.55 |
| 0.3-1.0 | 44 | 56.8% | -6.25 | 0.73 |

## Conviction by Direction

### LONG
| Conviction | Count | Win Rate | Avg PnL% |
|---|---|---|---|
| 80-101 | 3 | 0.0% | -30.59 |

### SHORT
| Conviction | Count | Win Rate | Avg PnL% |
|---|---|---|---|
| 40-60 | 55 | 63.6% | +1.27 |
| 80-101 | 22 | 63.6% | +16.42 |

## MarketAgent Confidence vs Outcome

| Mkt Confidence | Count | Win Rate | Avg PnL% |
|---|---|---|---|
| 0.6-0.7 | 75 | 58.7% | +2.03 |
| 0.7-0.85 | 5 | 100.0% | +37.46 |

## RiskAgent Confidence vs Outcome

| Risk Confidence | Count | Win Rate | Avg PnL% |
|---|---|---|---|
| 0.5-0.6 | 20 | 80.0% | +24.71 |
| 0.6-0.7 | 60 | 55.0% | -2.58 |

## Key Questions

**Does high conviction outperform low conviction?**
- High conviction (60+): 25 trades, 56.0% win rate
- Low conviction (<40): 0 trades, 0.0% win rate
- Verdict: YES — conviction is informative

**Does disagreement warn of lower-quality trades?**
- High disagreement (0.2+): 72 trades, 62.5% win rate
- Low disagreement (<0.1): 2 trades, 100.0% win rate
- Verdict: YES — disagreement is a useful warning
