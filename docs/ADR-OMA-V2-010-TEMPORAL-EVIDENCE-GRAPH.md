# ADR 010: temporal evidence graph

Status: experimental, additive; no trading or Criterion authority.

## Problem and decision
DecisionJournal preserves decisions and outcomes, but cannot reconstruct typed evidence paths. Add a provider-neutral SQLite graph with immutable JSON snapshots, explicit observation and availability timestamps, provenance, typed links and atomic batches. Reuse DecisionRecord and DecisionOutcome through explicit adapters. Do not replace existing scientific stores or execution authority.

An as-of query excludes nodes and links unavailable at the cutoff. An informs link must be available by the decision time. Unknown endpoints are rejected; missing information remains explicit in DecisionRecord. Evidence may link to one hypothesis in one direction. Contradictory updates require new snapshot identifiers. Outcome observations cannot precede their decision. Knowledge candidates are unreviewed and cannot carry promoted=true.

## Scope and limitations
This is an evidence graph, not a causal identification engine. Availability and provenance are caller attestations: the graph validates temporal consistency, not external truth. Production collectors must supply verified receipts. SQLite is not a tamper-evident chain, and no cross-database atomic transaction with DecisionJournal is claimed. The adapter is opt-in; existing runtime does not silently import arbitrary agent strings as Evidence. Source checksums identify files but do not establish original publication times.

The bundled case documents the failed 2024/2025 gate after observation. Its current import timestamps are not historical availability, and its hypothesis is a previously rejected claim rather than a preregistered forecast. Its outcome concerns documentation, not market performance. The unreviewed lesson candidate is not inserted into Knowledge or Criterion.

## Verification and next priorities
Tests cover a complete decision/outcome path, persistent as-of visibility, idempotence, invalid reference rejection, immutable conflicts, future evidence, endpoint types, outcome order, atomic rollback, evidence direction and prohibited promotion.

Priority 1: eligible host/feed preflight, then prospectively captured receipts under the frozen protocol. This external prerequisite remains blocked in this runtime by HTTP 451; do not bypass it.
Priority 2: wire verified receipt and scientific-store adapters into a single opt-in runtime case, including replay/export and reconciliation across stores. The present graph supplies the contract and retrospective example, not that operational integration.
Priority 3: evaluate the registered prospective cohort after duration and minimum-N gates; retain failures without retuning.
Priority 4: only eligible independent evidence may enter human-reviewed Criterion/prospective validation. Real execution needs separate risk, broker and reconciliation validation.
