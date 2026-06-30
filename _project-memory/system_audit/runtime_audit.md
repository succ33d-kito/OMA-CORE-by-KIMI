# Runtime Audit

## Configuration

- `.env` exists in the repository root. Values were not printed; existence alone is a security/runtime governance concern.
- `core/config/config.py` and dotenv loading exist.
- CLI initializes config, Telegram notifier, DB, monitor, event bus, council, agents, and scientific store.

## Logging and telemetry

- `core/utils/logger.py` and `core/monitoring/telemetry.py` exist.
- Telemetry is not shown as a production metrics backend.
- Alert routing is fragmented between notifier and monitoring modules.

## Health, failure, recovery

- `core/monitoring/health.py` and `failure_classifier.py` exist.
- Scripts include preflight/recovery/reality tests.
- No unified SRE runbook, restart policy, process supervisor, or durable queue was found.

## Persistence

```json
[
  {
    "path": "scientific.db",
    "size_bytes": 114688,
    "objects": [
      [
        "idx_criterion_deltas_created",
        "index"
      ],
      [
        "idx_criterion_deltas_dimension",
        "index"
      ],
      [
        "idx_criterion_deltas_status",
        "index"
      ],
      [
        "idx_evidence_direction",
        "index"
      ],
      [
        "idx_evidence_hypothesis",
        "index"
      ],
      [
        "idx_evidence_status",
        "index"
      ],
      [
        "idx_hypotheses_created",
        "index"
      ],
      [
        "idx_hypotheses_status",
        "index"
      ],
      [
        "idx_knowledge_confidence",
        "index"
      ],
      [
        "idx_knowledge_created",
        "index"
      ],
      [
        "idx_knowledge_expires",
        "index"
      ],
      [
        "idx_knowledge_status",
        "index"
      ],
      [
        "idx_outcome_comparisons_compared_at",
        "index"
      ],
      [
        "idx_outcome_comparisons_hypothesis",
        "index"
      ],
      [
        "idx_outcome_comparisons_verdict",
        "index"
      ],
      [
        "sqlite_autoindex_criterion_deltas_1",
        "index"
      ],
      [
        "sqlite_autoindex_evidence_1",
        "index"
      ],
      [
        "sqlite_autoindex_hypotheses_1",
        "index"
      ],
      [
        "sqlite_autoindex_knowledge_1",
        "index"
      ],
      [
        "sqlite_autoindex_outcome_comparisons_1",
        "index"
      ],
      [
        "criterion_deltas",
        "table"
      ],
      [
        "evidence",
        "table"
      ],
      [
        "hypotheses",
        "table"
      ],
      [
        "knowledge",
        "table"
      ],
      [
        "outcome_comparisons",
        "table"
      ]
    ],
    "counts": [
      [
        "criterion_deltas",
        0
      ],
      [
        "evidence",
        0
      ],
      [
        "hypotheses",
        0
      ],
      [
        "knowledge",
        0
      ],
      [
        "outcome_comparisons",
        0
      ]
    ]
  },
  {
    "path": "oma_core.db",
    "size_bytes": 1331200,
    "objects": [
      [
        "idx_events_processed",
        "index"
      ],
      [
        "idx_events_source",
        "index"
      ],
      [
        "idx_events_timestamp",
        "index"
      ],
      [
        "idx_events_type",
        "index"
      ],
      [
        "idx_events_urgency",
        "index"
      ],
      [
        "idx_opp_event",
        "index"
      ],
      [
        "idx_opp_score",
        "index"
      ],
      [
        "idx_opp_status",
        "index"
      ],
      [
        "sqlite_autoindex_events_1",
        "index"
      ],
      [
        "sqlite_autoindex_opportunities_1",
        "index"
      ],
      [
        "sqlite_autoindex_user_profiles_1",
        "index"
      ],
      [
        "events",
        "table"
      ],
      [
        "opportunities",
        "table"
      ],
      [
        "user_profiles",
        "table"
      ]
    ],
    "counts": [
      [
        "events",
        620
      ],
      [
        "opportunities",
        177
      ],
      [
        "user_profiles",
        0
      ]
    ]
  },
  {
    "path": "oma_core.db.backup_v20",
    "size_bytes": 4317184,
    "objects": [
      [
        "idx_events_processed",
        "index"
      ],
      [
        "idx_events_source",
        "index"
      ],
      [
        "idx_events_timestamp",
        "index"
      ],
      [
        "idx_events_type",
        "index"
      ],
      [
        "idx_events_urgency",
        "index"
      ],
      [
        "idx_opp_event",
        "index"
      ],
      [
        "idx_opp_score",
        "index"
      ],
      [
        "idx_opp_status",
        "index"
      ],
      [
        "sqlite_autoindex_events_1",
        "index"
      ],
      [
        "sqlite_autoindex_opportunities_1",
        "index"
      ],
      [
        "sqlite_autoindex_user_profiles_1",
        "index"
      ],
      [
        "events",
        "table"
      ],
      [
        "opportunities",
        "table"
      ],
      [
        "user_profiles",
        "table"
      ]
    ],
    "counts": [
      [
        "events",
        1571
      ],
      [
        "opportunities",
        692
      ],
      [
        "user_profiles",
        0
      ]
    ]
  }
]
```

SQLite local DBs are present in the repository. This is acceptable for experiments but not production-grade as-is.

## Graceful shutdown / resume

- CLI `watch` mode uses an infinite loop and `KeyboardInterrupt` handling.
- Resume guarantees and exactly-once processing are not proven.

## File growth / JSONL growth

- `_project-memory`, runtime reports, logs, DB backups, and score calibration outputs exist.
- Retention policy is unclear.

## Thread safety

- Event bus appears in-process; thread-safety/delivery guarantees require dedicated testing.
- SQLite connection scope exists but concurrent writer policy is not proven.

## Runtime verdict

Runtime maturity is experimental-to-internal. The codebase can run workflows locally, but production runtime controls are incomplete.
