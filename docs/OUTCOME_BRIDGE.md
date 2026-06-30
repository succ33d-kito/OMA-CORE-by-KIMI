# Outcome Bridge Architecture

## Purpose

The Outcome Bridge converts operational opportunities from `oma_core.db` into
scientific hypotheses in `scientific.db`. It is the first link between the
Operational Layer and the Scientific Layer.

## Data Flow

```
Opportunity (oma_core.db) → OutcomeBridge → Hypothesis (scientific.db)
```

## Field Mapping

| Opportunity Field       | Hypothesis Field          | Transformation                    |
|------------------------|--------------------------|-----------------------------------|
| id / event_id          | id                       | `hyp_{event_id}`                  |
| title                  | title                    | `[BRIDGE] {type}: {title[:60]}`   |
| description            | description              | Combined with conditions          |
| action_suggested       | predicted_consequence    | Direction + action description    |
| score / conviction     | confidence               | `conviction / 100`                |
| opportunity_type       | embedded in conditions   | Used for direction mapping        |
| assets                 | embedded in conditions   | Concatenated string               |
| timestamp              | embedded in conditions   | ISO format timestamp              |

## Direction Mapping

Each opportunity type maps to a predicted market direction:

- `LONG_SETUP` → bullish
- `SHORT_SETUP` → bearish
- `MOMENTUM_PLAY` → momentum
- `SAFE_HAVEN_FLOW` → risk_off
- `WHALE_ACCUMULATION` → bullish
- (20+ additional mappings in `TYPE_DIRECTION_MAP`)

## Status Lifecycle

1. `FORMULATED` — Created by bridge (initial state)
2. `ACTIVE` — Ready for testing (manual transition)
3. `EVALUATED` — Outcome compared
4. `ARCHIVED` — No longer relevant

## Safety

- Never modifies operational database
- Never modifies execution
- Dry-run by default (`--commit` required to persist)
- Duplicate detection by hypothesis ID prefix
