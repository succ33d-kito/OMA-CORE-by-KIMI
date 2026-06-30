# Learning Workflow

## Complete Lifecycle

```
Opportunity → Hypothesis → Outcome → Evidence → Knowledge → Criterion Delta
     (O1)         (O2)         (O3)        (O4)         (PENDING_REVIEW)
```

## Step 1: Ingest (O1)

Convert opportunities to hypotheses:

```bash
oma lab ingest
oma lab ingest --commit  # Write to scientific.db
oma lab ingest --min-score 50 --limit 10
```

## Step 2: Evaluate (O2)

Compare hypotheses against actual outcomes:

```bash
oma lab evaluate --actual-outcome "Bitcoin rose 3% after Fed announcement"
oma lab evaluate -H <hypothesis_id> -O "Market dropped 2%" --commit
```

Verdict states:
- `CONFIRMED` — Prediction matched reality
- `PARTIALLY_CONFIRMED` — Partial match
- `REJECTED` — Prediction was wrong
- `INCONCLUSIVE` — Cannot determine

## Step 3: Extract Knowledge (O3)

Convert confirmed outcomes into reusable Knowledge objects:

```bash
oma lab knowledge extract --statement "..." --evidence-summary "..." --conditions "..." --scope crypto --time-horizon swing
oma lab knowledge list
oma lab knowledge show <id>
```

## Step 4: Generate Criterion Candidates (O4)

Automatically detect patterns and propose criterion deltas:

```python
from core.scientific.criterion_candidate_generator import CriterionCandidateGenerator
gen = CriterionCandidateGenerator()
result = gen.run_pipeline(dry_run=True)
```

All candidates are `PENDING_REVIEW` — never auto-applied.

## CLI Reference

```bash
oma lab ingest       # Bridge opportunities → hypotheses
oma lab evaluate     # Evaluate hypotheses against outcomes
oma lab knowledge    # Manage knowledge items
oma lab criterion    # Manage criterion deltas
oma lab report       # Learning telemetry
oma lab status       # Current lab state
```

All commands are read-only by default. Use `--commit` to persist changes.
