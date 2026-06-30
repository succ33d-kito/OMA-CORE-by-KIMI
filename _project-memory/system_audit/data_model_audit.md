# Data Model Audit

## Schema/model files

| File | Classes | Function count |
|---|---|---|
| core/execution_engine/schemas/__init__.py |  | 0 |
| core/execution_engine/schemas/execution.py | ExecutionRequest, ExecutionOrder, ExecutionPosition, ExecutionPortfolio, ExecutionLedgerRecord, ExecutionResult, ExecutionSummary, ExecutionReport | 0 |
| core/outcome_domain/__init__.py |  | 0 |
| core/outcome_domain/collector.py | OutcomeCollector | 16 |
| core/outcome_domain/errors.py | OutcomeValidationError | 1 |
| core/outcome_domain/outcome.py | Outcome | 0 |
| core/schemas/__init__.py |  | 0 |
| core/schemas/agent_schema.py | AgentRole, CouncilTier, Recommendation, AgentOpinion, CouncilDecision | 4 |
| core/schemas/criterion_delta_schema.py | DeltaStatus, CriterionDelta | 2 |
| core/schemas/event_schema.py | EventType, AssetClass, Sentiment, Urgency, Asset, Event | 3 |
| core/schemas/evidence_schema.py | EvidenceDirection, EvidenceStatus, Evidence | 2 |
| core/schemas/hypothesis_schema.py | HypothesisStatus, Hypothesis | 2 |
| core/schemas/knowledge_schema.py | KnowledgeStatus, Knowledge | 2 |
| core/schemas/outcome_comparison_schema.py | Verdict, ErrorType, ComparisonType, OutcomeComparison | 2 |
| core/schemas/trade_schema.py | TradeDirection, TradeStatus, ExitReason, TradeSignal, Trade | 4 |


## Key findings

- Multiple schema regimes exist: legacy `core/schemas`, governed Execution Engine schemas, and Outcome Domain object definitions.
- Several objects are dataclasses, but validation levels vary by module.
- Canonical docs define object ownership more clearly than older code does.
- `setup.py` embeds an older copy of several schema/database/collector/engine files, creating a major confusion risk.
- Runtime DB schemas exist as SQL strings and table initialization logic rather than migrations.

## Naming/version mismatch risks

- `ExecutionResult`, `Outcome`, `Evidence`, `Knowledge`, `Criterion` are governed concepts, but some scientific code predates newest Outcome Domain boundaries.
- `OutcomeComparison` and outcome evaluator/bridge code should be reviewed against `OUTCOME_ARCHITECTURE_V1.md` and `SCIENTIFIC_BRIDGE_ARCHITECTURE_V1.md` before further certification.

## Duplicated/dead fields risk

A full field-by-field semantic review should compare `OBJECT_MODEL_V1.md` to every dataclass in `core/schemas`, `core/execution_engine/schemas`, and `core/outcome_domain`. Current evidence suggests overlap but not yet a single enforced schema registry.
