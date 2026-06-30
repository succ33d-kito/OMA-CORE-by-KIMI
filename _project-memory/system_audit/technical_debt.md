# Technical Debt Register

| Rank | Category | Debt | Evidence | Impact | Recommendation |
|---|---|---|---|---|---|
| Critical | Architecture | Legacy `core/execution` coexists with governed `core/execution_engine` | Both directories exist and tests cover both | Confused execution authority | Freeze legacy path or create migration ADR |
| Critical | Risk | No proven mandatory risk gate across every execution path | Fragmented RiskAgent/guards/execution | Live trading danger | Define single pre-execution risk authority |
| Critical | Security | `.env` and DB/runtime files in repo root | Repository inventory | Secret/state leakage risk | Remove from repo, add secret scanning |
| High | Architecture | CLI is monolithic composition root | `core/cli/main.py` 1115 lines | Fragile startup/import coupling | Split command modules after governance |
| High | Runtime | No durable queue/replay/backpressure | Event bus in-process | Lost/duplicated events | Design runtime envelope before production |
| High | Data | Schema/object duplication | `core/schemas`, execution schemas, outcome domain | Inconsistent contracts | Canonical schema registry |
| High | Testing | No end-to-end canonical OSIRIS flow test | Tests are unit/domain-oriented | Integration regressions | Add full pipeline acceptance test |
| High | Dependencies | Duplicate/unpinned requirements | requirements.txt | Repro/security risk | Lock/pin dependencies |
| Medium | Monitoring | Telemetry exists but no SLO/backend | monitoring modules | Hard to operate | Define observability contract |
| Medium | Generated files | Generated/runtime artifacts mixed with source | pycache, DBs, reports | Repo hygiene risk | Artifact retention policy |
| Medium | Scientific | Scientific code may predate new governance | outcome bridge/evaluator exist | Boundary drift | Re-certify under Scientific Bridge sprint |
| Medium | Performance | Blocking synchronous network/runtime loops | watch mode/network clients | Scale limits | Async/job orchestration later |
| Low | Documentation | Lots of docs, some possibly stale | docs/ and untracked state | Cognitive load | Governance index/status page |
