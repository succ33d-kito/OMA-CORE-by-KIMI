# Test Coverage Audit

## Test inventory

- Test files: **48**
- Full suite result during audit: **908 passed, 3 warnings in 143.92s**
- Warnings: pytest deprecation warnings in paper trading experiment class-scoped fixture usage.

## Coverage by subsystem

| Subsystem tag | Tests | Files |
|---|---|---|
| agent | 4 | test_market_agent_signal_integrity.py<br>test_agent_council.py<br>test_market_agent.py<br>test_risk_agent.py |
| backtest | 1 | test_backtest_v2.py |
| collector | 2 | test_outcome_collector_15e.py<br>test_fred_collector.py |
| council | 1 | test_council_v2.py |
| criterion | 1 | test_criterion_candidate_generator.py |
| event | 1 | test_event_bus.py |
| execution | 4 | test_execution_lifecycle_15b.py<br>test_execution_order_ledger_15c.py<br>test_execution_engine_foundation.py<br>test_execution_state_15d.py |
| knowledge | 1 | test_knowledge_extractor.py |
| learning | 2 | test_historical_learning_replay.py<br>test_learning_core.py |
| memory | 2 | test_performance_memory.py<br>test_memory.py |
| misc | 19 | test_integration.py<br>test_audit_conviction.py<br>test_extended_demo_telemetry.py<br>test_audit_pipeline_backlog.py<br>test_telegram_notifier.py<br>test_read_only_operational_integration.py<br>test_oma_launcher.py<br>__init__.py<br>test_crypto_regression.py<br>test_cleanup_pre_guard_artifacts.py<br>test_survival_replay.py<br>test_yahoo_data_guard.py<br>test_kill_switch.py<br>test_failure_classifier.py<br>test_audit_priority_consistency.py<br>test_lab.py<br>test_knife_detector.py<br>test_crash_detector_v2.py<br>__init__.py |
| monitor | 1 | test_health_monitor.py |
| outcome | 2 | test_outcome_bridge.py<br>test_evaluate_outcomes.py |
| paper | 1 | test_paper_trading_experiment.py |
| profile | 1 | test_profiles.py |
| schema | 2 | test_trade_schema.py<br>test_agent_schema.py |
| scientific | 1 | test_scientific_layer.py |
| score | 2 | test_score_saturation_audit.py<br>test_score_calibration.py |


## Strengths

- The repository has a large passing test suite.
- Execution Engine governance tests are detailed and layered.
- Outcome Domain tests validate isolation, determinism, immutability, completeness, traceability, and failures.
- Risk/trading guard tests exist.
- Scientific/lifecycle tests exist.

## Gaps

- No measured coverage report tool is installed in the venv (`coverage` unavailable).
- Full canonical end-to-end integration test is missing: collector → validation → event bus → agents → council → risk → execution_engine → outcome_domain → scientific_bridge.
- Stress, chaos, concurrency, file-growth, restart/resume, and long-running soak tests are missing or not evident.
- Tests are strong for deterministic units but weak for distributed/runtime properties.
- Several tests validate artifacts/scripts rather than production service behaviour.

## Brittle/weak tests

- Some test files include placeholder/pass patterns.
- Some tests likely rely on sample fixtures and mocked behavior rather than live source variability.
- Paper trading experiment tests emit pytest deprecation warnings.

## Critical paths without sufficient proof

- Unified risk gate before any execution.
- Durable event bus/replay.
- Database migration and corruption recovery.
- CLI long-running watch mode shutdown/resume.
- Multi-market production execution.
- Scientific bridge canonical handoff.
