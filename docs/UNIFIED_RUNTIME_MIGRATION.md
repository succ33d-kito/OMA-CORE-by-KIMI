# Unified runtime / OSIRIS boundary — Window #4.5

OSIRIS observes; it does not govern. The new path is configured canonical evidence
→ read-only adapters → immutable SystemSnapshot → CLI and GET /api/system → Mission
Control. It never invokes capture, decision generation, execution or repair.

## Boundary inventory

| Existing component | Classification | Boundary / evidence |
|---|---|---|
| WorldMonitorV2 | KEEP | Existing explicit collect/watch operations only; collect_all invokes collectors. Never imported by the system-status dispatch. |
| Pipeline / ScoreEngine / OpportunityEngine | DO_NOT_USE_AS_AUTHORITY | Heuristic scores and persisted legacy opportunities are not causal WorldState/Radar/validated economic probabilities. Opportunity generation writes the legacy DB. |
| oma_core.db / OMACoreDatabase | DO_NOT_USE_AS_AUTHORITY | Constructor initializes schema. It is not a PIT or shadow decision ledger. New API does not construct it. |
| Existing dashboard endpoints | DEPRECATE_LATER | Preserved under their original API URLs and /legacy page; initialization is lazy and confined to legacy access. Their semantics do not enter SystemSnapshot. |
| old oma run | KEEP | Still collects, processes and can notify Telegram. New `system status` dispatch occurs before those imports or object construction. |
| Legacy execution/slippage and paper trading | DO_NOT_USE_AS_AUTHORITY | Configured execution costs / simulation are not factual venue execution receipts. No runtime adapters import them. |
| Dashboard shell | ADAPT | Root now renders read-only Mission Control; only GET /api/system provides its data. |
| Price continuity | ADAPT | Explicit read_only path opens observations using SQLite mode=ro; existing scientific continuity algorithm is reused. No schema initialization or anchor writing. |
| WorldState / Radar / shadow ledger | KEEP | Existing persisted identities and commitments supply observational summaries. No ranking or decision is recomputed. |
| Window #4R execution/position plane | KEEP | Intents remain non-executed, positions pending. Missing estimate/position stores stay unknown rather than inferred from plans. |

## Operator usage and source configuration

Equivalent CLI: `python -m core.cli.main system status [--config PATH] [--json]`.
`python -m core.runtime.cli status` is also available. `--at` accepts an explicit
aware timestamp for reproducible inspection. Otherwise the snapshot uses UTC now.
The dashboard reads the same configuration from `OMA_RUNTIME_CONFIG` or its Flask
configuration. No default storage location is guessed. With no configuration,
the node is LOCAL_UNCONFIGURED and sources are UNAVAILABLE.

Configuration is local JSON, not operational data for Git:

```json
{
  "node_id": "LAPTOP",
  "sources": [
    {"name":"price", "kind":"price", "path":"ABSOLUTE_PRICE_LEDGER_PATH",
     "node_id":"LAPTOP", "auxiliary":"ABSOLUTE_PRICE_STATE_DIRECTORY", "max_age_seconds":7200}
  ]
}
```

The example freshness limit is an explicit operator choice, not a scientific or
trading threshold. Without a limit, freshness remains UNKNOWN. Source references
use node/name; physical paths remain in the operator's configuration, not evidence
identity. Keep this configuration alongside local operational storage, outside Git.

Supported descriptors:

| kind | path | auxiliary |
|---|---|---|
| price | Existing observations SQLite ledger | Existing Price state directory |
| collector | Sealed multi-market health.json | None |
| book / premium | Existing capture cycle directory | Frozen universe directory |
| world / radar | Existing radar run directory with result/world/radar JSON | None |
| shadow | Existing shadow_decisions.sqlite | None |
| execution | Existing #4R run-ID JSON artifact | None |
| position | No canonical persistent adapter yet; present parseable input yields UNKNOWN | None |

World/Radar summaries can also project from the verified shadow ledger if no
direct source was configured. Corrupt direct sources are never replaced with
fallback data. Portfolio/Risk/Allocation/Thesis/Forecast summaries come from the
same historical decision, not an assertion of live portfolio inventory. There is
no Event adapter yet. Unsupported configured sources fail visibly.

A collector's reported PID/RUNNING/next cycle is historical report data, not an
OS process liveness check. Global runtime mode remains UNKNOWN; individual shadow
artifacts retain SHADOW. A stale record never proves current runtime health.
81H input readiness is shown only from current verified Price continuity; it is
not Regime validation. Confirmation/holdouts are not inspected.

Each independent node requires its own configuration and snapshot. WORK-PC paths
are not hardcoded or merged into laptop SQLite. This version does not retrieve
remote nodes over the network. Never copy a remote ledger into the local writer.

## Future cutover (not activated here)

1. Configure and verify each actual node's read-only sources, including provenance,
   freshness, corruption and no-write checks against deployed storage.
2. Compare observable coverage with operator needs. Implement missing adapters only
   once a canonical persisted contract exists; do not infer fills or open positions.
3. Explicitly approve a later cutover of legacy operator entry points. Preserve
   archived legacy semantics and keep capture/execution controls outside GET/UI.
4. Deprecate the legacy dashboard only after replacement coverage is demonstrated.

No runtime deployment, collector activation, real execution, economic winner,
Edge, Regime or Mechanics validation is claimed by this window.
