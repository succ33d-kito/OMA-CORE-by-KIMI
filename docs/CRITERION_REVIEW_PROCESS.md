# Criterion Review Process

## Principle

Criterion deltas are NEVER auto-applied. Human review is always required
(ARCHITECTURE V2 Invariant 1).

## Candidate Generation

The `CriterionCandidateGenerator` analyzes outcome patterns and proposes deltas
across 8 criterion dimensions:

| Dimension               | Description                                  |
|------------------------|----------------------------------------------|
| hypothesis_quality      | Quality of hypothesis formulation            |
| evidence_quality        | Quality of supporting evidence               |
| decision_quality        | Quality of decisions                         |
| calibration             | Prediction calibration accuracy              |
| error_recurrence        | Patterns in error types                      |
| knowledge_yield         | Rate of knowledge extraction                 |
| learning_velocity       | Speed of learning                            |
| scarce_resource_conversion | Resource efficiency                       |

## Review Process

1. **Generate**: Run `CriterionCandidateGenerator.run_pipeline()` or observe via CLI
2. **Review**: List pending candidates
3. **Approve or Reject**: Manual decision via CLI
4. **Track**: All decisions are recorded for audit

## CLI Commands

```bash
oma lab criterion list              # Show all deltas (filter by --status, --dimension)
oma lab criterion list --status pending_review  # Show only pending
oma lab criterion show <id>         # Show delta details
oma lab criterion approve <id>      # Approve and apply
oma lab criterion reject <id>       # Reject
```

## Safety

- All deltas start as `PENDING_REVIEW`
- `applied_at` timestamp recorded on approval
- `outcome_tracking` captures results of applied deltas
- No operational criteria are modified without explicit human confirmation
