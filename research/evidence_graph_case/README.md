# Temporal evidence case

Retrospective governance example of the failed derivatives stability gate. `case.json` is the portable graph; `case.sqlite` is its rebuildable query store. `manifest.json` pins the source report and JSON hash. No forecast or historical availability is claimed. No promotion is performed.

Rebuild from the repository root with the exact command in manifest.json. Repeating the command against the existing database is idempotent. Changing source content or import time requires a new output directory rather than overwriting immutable IDs.

The graph demonstrates source → event → hypothesis/evidence → research decision → documentation outcome → unreviewed candidate. As-of queries at the decision timestamp omit the later outcome and candidate. Provenance is explicit; missing data is not imputed.
