# Security Audit

## Pattern scan summary

| Pattern | Hits | Examples |
|---|---|---|
| secret_refs | 259 | scripts/asset_coverage_audit.py:24 # BinanceCollector<br>scripts/asset_coverage_audit.py:25 binance_symbols =***REDACTED***<br>scripts/asset_coverage_audit.py:30 collectors["binance"] =***REDACTED***<br>scripts/asset_coverage_audit.py:32 "symbols": [s.replace("USDT", "") for s in binance_symbols],<br>scripts/asset_coverage_audit.py:33 "raw_symbols": binance_symbols,<br>scripts/asset_coverage_audit.py:34 "count": len(binance_symbols),<br>scripts/asset_coverage_audit.py:131 # MarketAgent._fetch_ohlcv: Binance first, then yfinance<br>scripts/asset_coverage_audit.py:133 binance_symbols =***REDACTED***<br>scripts/asset_coverage_audit.py:142 "native_binance_support": {<br>scripts/asset_coverage_audit.py:144 "symbols": list(binance_symbols.keys()),<br>scripts/asset_coverage_audit.py:145 "count": len(binance_symbols),<br>scripts/asset_coverage_audit.py:146 "note": "Agents try Binance first. Only crypto symbols have native support.", |
| subprocess | 5 | scripts/check_oma_launcher.py:18 import subprocess<br>tests/test_oma_launcher.py:127 import subprocess<br>tests/test_oma_launcher.py:128 result = subprocess.run(["bash", script_path], capture_output=True, text=True, timeout=10)<br>tests/test_oma_launcher.py:154 import subprocess<br>tests/test_oma_launcher.py:155 result = subprocess.run(["bash", script_path], capture_output=True, text=True, timeout=10) |
| shell_true | 0 |  |
| os_system | 0 |  |
| eval | 0 |  |
| exec | 0 |  |
| pickle | 0 |  |
| yaml_load | 0 |  |
| bare_except | 29 | export_for_github.py:34 except:<br>export_for_github.py:39 except:<br>render_app.py:32 except: opp['assets'] = [opp['assets']]<br>render_app.py:35 except: opp['action_details'] = {"timeframe": "N/A", "rationale": ""}<br>setup.py:284 except: data[field] = []<br>setup.py:288 except: data["metadata"] = {}<br>setup.py:536 except:<br>scripts/survival_and_short.py:34 except: pass<br>scripts/slippage_test.py:37 except: pass<br>scripts/slippage_test.py:45 except: pass<br>backups/v2.0/backtest_engine.py:143 except:<br>backups/v2.0/backtest_engine.py:146 except: |
| broad_except | 95 | render_app.py:43 except Exception as e:<br>migrate_to_postgres.py:73 except Exception as e:<br>setup.py:195 except Exception as e:<br>setup.py:342 except Exception as e:<br>setup.py:448 except Exception as e:<br>setup.py:678 except Exception as e:<br>setup.py:781 except Exception as e:<br>dashboard/app.py:32 except Exception as e:<br>dashboard/app.py:45 except Exception as e:<br>dashboard/app.py:61 except Exception as e:<br>scripts/regime_robustness.py:111 except Exception as e:<br>scripts/research_sprint.py:66 except Exception as e: |


## Secrets

- `.env` exists in repository root. Contents were not printed. This must be treated as sensitive.
- Telegram and Binance environment variable references exist.
- No hardcoded secret values are reported here; secret values were intentionally redacted from scan examples.

## Unsafe execution / serialization

- Subprocess usage exists in scripts/tests.
- `shell=True`, `eval`, `exec`, and pickle hits should be reviewed before production use. Pattern scan counts above are static and require manual triage.
- Bare/broad exception handling exists and can hide failures.

## Unsafe file access

- CLI export writes files in current working directory.
- DB files live in repository root.
- Generated reports and runtime state are mixed with source tree.

## Security verdict

Security posture is acceptable for local research but not production. Required next steps: remove secrets from repo tree, add secret scanning, pin dependencies, run Bandit/pip-audit, centralize subprocess/file write policy, and add permission boundaries for live execution paths.
