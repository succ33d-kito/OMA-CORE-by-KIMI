# Repository Map — O.M.A.-C.O.R.E. / OSIRIS System Audit

**Audit type:** repository discovery, evidence-first.  
**Scope:** static repository files plus local test/runtime artifacts.  
**Generated under:** `_project-memory/system_audit/`.

## Top-level inventory

- Total non-venv/non-git files scanned: **371**
- Python files: **200**
- Markdown files: **141**
- Tests: **48**
- Core Python files: **113**
- Script Python files: **32**

## Top-level folders / files

| Path | File count |
|---|---|
| core | 113 |
| docs | 93 |
| _project-memory | 56 |
| tests | 47 |
| scripts | 33 |
| _live_paper_gate | 4 |
| dashboard | 3 |
| backups | 3 |
| research | 2 |
| .hermes | 2 |
| export_for_github.py | 1 |
| smoke.log | 1 |
| render_app.py | 1 |
| migrate_to_postgres.py | 1 |
| oma cmd | 1 |
| IDEA.md | 1 |
| scientific.db | 1 |
| oma_core.db | 1 |
| .env | 1 |
| run_oma_cron.sh | 1 |
| oma_core.db.backup_v20 | 1 |
| setup.py | 1 |
| .gitignore | 1 |
| requirements.txt | 1 |
| fixtures | 1 |


## File extensions

| Extension | Count |
|---|---|
| .py | 200 |
| .md | 141 |
| .json | 15 |
| <none> | 3 |
| .sh | 3 |
| .db | 2 |
| .html | 2 |
| .zip | 2 |
| .log | 1 |
| .backup_v20 | 1 |
| .txt | 1 |


## Core modules

| core/<module> | Python file count |
|---|---|
| execution_engine | 22 |
| scientific | 13 |
| collectors | 12 |
| execution | 10 |
| markets | 9 |
| schemas | 9 |
| agents | 6 |
| engines | 5 |
| monitoring | 4 |
| outcome_domain | 4 |
| council | 3 |
| cli | 2 |
| utils | 2 |
| event_bus | 2 |
| profiles | 2 |
| memory | 2 |
| config | 2 |
| database | 2 |
| __init__.py | 1 |
| processors | 1 |


## Entry points and scripts

- Primary CLI surface: `core/cli/main.py` (**1115 lines**).
- CLI command methods detected: `cmd_collect, cmd_council, cmd_events, cmd_evidence, cmd_evidence_add, cmd_evidence_list, cmd_export, cmd_hypothesis, cmd_hypothesis_archive, cmd_hypothesis_create, cmd_hypothesis_list, cmd_hypothesis_show, cmd_hypothesis_transition, cmd_lab, cmd_lab_compare, cmd_lab_criterion, cmd_lab_evaluate, cmd_lab_ingest, cmd_lab_knowledge, cmd_lab_report, cmd_lab_status, cmd_opportunities, cmd_process, cmd_run, cmd_scientific_status, cmd_status, cmd_watch`.
- `run_oma_cron.sh` exists and is a runtime launcher surface.
- `render_app.py`, `dashboard/`, and `scripts/` provide auxiliary runtime/demo/audit surfaces.
- `setup.py` is **not normal package metadata**; it is a large bootstrap/source-generation style script containing embedded project files. Treat it as legacy/generated-risk until reviewed.

## Tests

| Area | Test files | Examples |
|---|---|---|
| agent | 4 | test_market_agent_signal_integrity.py, test_agent_council.py, test_market_agent.py, test_risk_agent.py |
| backtest | 1 | test_backtest_v2.py |
| collector | 2 | test_outcome_collector_15e.py, test_fred_collector.py |
| council | 1 | test_council_v2.py |
| criterion | 1 | test_criterion_candidate_generator.py |
| event | 1 | test_event_bus.py |
| execution | 4 | test_execution_lifecycle_15b.py, test_execution_order_ledger_15c.py, test_execution_engine_foundation.py, test_execution_state_15d.py |
| knowledge | 1 | test_knowledge_extractor.py |
| learning | 2 | test_historical_learning_replay.py, test_learning_core.py |
| memory | 2 | test_performance_memory.py, test_memory.py |
| misc | 19 | test_integration.py, test_audit_conviction.py, test_extended_demo_telemetry.py, test_audit_pipeline_backlog.py, test_telegram_notifier.py, test_read_only_operational_integration.py, test_oma_launcher.py, __init__.py, test_crypto_regression.py, test_cleanup_pre_guard_artifacts.py |
| monitor | 1 | test_health_monitor.py |
| outcome | 2 | test_outcome_bridge.py, test_evaluate_outcomes.py |
| paper | 1 | test_paper_trading_experiment.py |
| profile | 1 | test_profiles.py |
| schema | 2 | test_trade_schema.py, test_agent_schema.py |
| scientific | 1 | test_scientific_layer.py |
| score | 2 | test_score_saturation_audit.py, test_score_calibration.py |


## Runtime/generated files found

- `oma_core.db`, `scientific.db`, `oma_core.db.backup_v20` are repository-local DB/runtime artifacts.
- `.pytest_cache/`, `__pycache__/`, `.hermes/desktop-attachments/`, `_project-memory/score_calibration/`, `_live_paper_gate/`, `smoke.log` are generated/runtime or local memory artifacts.
- These should not be treated as canonical source unless explicitly governed.

## Duplicate/legacy candidates

### Duplicate basenames

| Basename | Paths |
|---|---|
| CAPABILITY_MATURITY.md | docs/CAPABILITY_MATURITY.md<br>docs/capabilities/CAPABILITY_MATURITY.md |
| backtest_engine.py | backups/v2.0/backtest_engine.py<br>core/engines/backtest_engine.py |
| errors.py | core/execution_engine/exceptions/errors.py<br>core/outcome_domain/errors.py |
| index.html | docs/index.html<br>dashboard/templates/index.html |
| score_opportunity.py | backups/v2.0/score_opportunity.py<br>core/engines/score_opportunity.py |
| setup.py | setup.py<br>backups/v2.0/setup.py |
| states.py | core/execution_engine/positions/states.py<br>core/execution_engine/orders/states.py |


### Duplicate file content groups

| Group | Files |
|---|---|
| 1 | .hermes/desktop-attachments/OMA_CORE_Knowledge_Pack_v0_1.zip<br>.hermes/desktop-attachments/OMA_CORE_Knowledge_Pack_v0_1-2.zip |
| 2 | core/cli/__init__.py<br>core/utils/__init__.py<br>core/monitoring/__init__.py<br>core/database/__init__.py<br>core/processors/__init__.py |


## Git status at audit time

```text
M core/cli/main.py
 M core/engines/score_opportunity.py
 M core/schemas/outcome_comparison_schema.py
 M core/scientific/scientific_store.py
 M run_oma_cron.sh
 M scripts/audit_score_saturation.py
 M tests/test_learning_core.py
?? .hermes/
?? IDEA.md
?? _project-memory/score_calibration/
?? core/execution_engine/
?? core/outcome_domain/
?? core/scientific/criterion_candidate_generator.py
?? core/scientific/knowledge_extractor.py
?? core/scientific/outcome_bridge.py
?? core/scientific/outcome_evaluator.py
?? docs/ARCHITECTURE_DECISIONS.md
?? docs/CAPABILITY_DEMONSTRATION_15B.md
?? docs/CAPABILITY_DEMONSTRATION_15C.md
?? docs/CAPABILITY_DEMONSTRATION_15D.md
?? docs/CAPABILITY_DEMONSTRATION_15E.md
?? docs/CAPABILITY_GAP_ANALYSIS_STANDARD.md
?? docs/CAPABILITY_MATURITY.md
?? docs/CRITERION_REVIEW_PROCESS.md
?? docs/ENGINEERING_CONSTITUTION.md
?? docs/ENGINEERING_DISCOVERY_PROTOCOL.md
?? docs/ENGINEERING_MANIFESTO.md
?? docs/ENGINEERING_METRICS.md
?? docs/IMPLEMENTATION_AUTHORIZATION_STANDARD.md
?? docs/IMPLEMENTATION_STRATEGY_V1.md
?? docs/INTEGRATION_ARCHITECTURE_V1.1.md
?? docs/INTEGRATION_ARCHITECTURE_V1.md
?? docs/LEARNING_WORKFLOW.md
?? docs/OBJECT_MODEL_V1.md
?? docs/OUTCOME_ARCHITECTURE_V1.md
?? docs/OUTCOME_BRIDGE.md
?? docs/PIPELINE_V2.md
?? docs/REPOSITORY_DISCOVERY_STANDARD.md
?? docs/SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md
?? docs/SPRINT13_FINAL_REPORT.md
?? docs/SPRINT15A_ENGINEERING_REVIEW.md
?? docs/SPRINT15B_ENGINEERING_REVIEW.md
?? docs/SPRINT15C_ENGINEERING_REVIEW.md
?? docs/SPRINT15D_ENGINEERING_REVIEW.md
?? docs/SPRINT15E_ENGINEERING_REVIEW.md
?? docs/capabilities/
?? scripts/evaluate_outcomes.py
?? tests/test_criterion_candidate_generator.py
?? tests/test_evaluate_outcomes.py
?? tests/test_execution_engine_foundation.py
?? tests/test_execution_lifecycle_15b.py
?? tests/test_execution_order_ledger_15c.py
?? tests/test_execution_state_15d.py
?? tests/test_knowledge_extractor.py
?? tests/test_outcome_bridge.py
?? tests/test_outcome_collector_15e.py
?? tests/test_score_calibration.py
```
