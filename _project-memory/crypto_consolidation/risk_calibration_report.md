# OSIRIS Risk Calibration Audit Report
> Generated: 2026-06-23 02:39:04 UTC
> Trades analyzed: 54

## Methodology
Trades are bucketed by risk score. For each bucket we measure average loss,
tail loss, max adverse excursion, stop hit rate, and drawdown contribution.

---

## Risk Score Bucket Analysis

| Risk Score | Count | Win Rate | Avg PnL% | Avg Loss% | Tail Loss (95th) | Max Loss% | Stop Hit Rate |
|---|---|---|---|---|---|---|---|
| 80-101 | 54 | 57.4% | +11.22 | -20.54 | -0.34 | -40.95 |

## ATR% vs Realized Loss

| ATR% Range | Count | Avg Loss% | Max Loss% |
|---|---|---|---|
| 5-100% | 54 | -20.54 | -40.95 |

## Volatility vs Realized Loss

| Annualized Vol% | Count | Avg PnL% | Avg Loss% | Max Loss% |
|---|---|---|---|---|
| 100-1000% | 54 | +11.22 | -20.54 | -40.95 |

## Key Questions

**Do higher risk scores predict larger losses?**
- High risk (60+): 54 trades, avg loss -20.54%
- Low risk (<30): 0 trades, avg loss +0.00%
- Verdict: YES — risk score correlates with loss severity
