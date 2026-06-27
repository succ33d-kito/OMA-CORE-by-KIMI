# Implementation Decision Log

## Permanent Record of Engineering Decisions

*Created: June 2026 — ERA II Iteration 1*

---

## Purpose

Every architectural simplification, deferral, and design choice in ERA II is documented here with its rationale, alternatives considered, and conditions for future re-evaluation.

This document exists because:

1. **Memory fades.** Six months from now, the reasoning behind a decision will not be obvious from the code alone.
2. **Decisions accumulate.** A decision that is correct today may become incorrect as the system evolves. Without documentation, future contributors cannot know when to revisit it.
3. **Complexity must be justified.** The Constitution (Article 4) and Implementation Bridge (Invariant 7) require every complexity decision to carry its own justification.

---

## Decision ID-001: Merged Hypothesis + Evidence into One Iteration

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** Hypothesis and Evidence were implemented together in a single iteration, rather than sequentially in two separate iterations.

**Context:** The original Implementation Bridge (03_IMPLEMENTATION_BRIDGE.md §5.2–5.3) specified Iteration 1 as Hypothesis Foundation and Iteration 2 as Evidence Tracking. The self-review (S-02) challenged this separation: "Hypothesis and Evidence are conceptually connected. A hypothesis without evidence is an opinion. Building them in separate iterations may produce a Hypothesis that cannot be evaluated."

**Alternatives Considered:**
- **Sequential (original plan):** Hypothesis first, Evidence second. Risk: hypotheses would exist temporarily without evidence support, creating orphan records.
- **Sequential with gate:** Hypothesis first, but block ACTIVE transition until Evidence exists. Risk: adds complexity to state machine to enforce cross-object constraint.
- **Merged (chosen):** Both implemented together. Evidence addable immediately. Hypothesis lifecycle requirement ("evidence before FORMULATED") is mental/process-based, not code-enforced.

**Evidence:** The Implementation Bridge self-review explicitly recommended the merge. No evidence suggests sequential implementation would produce better outcomes.

**Reasoning:** The conceptual dependency (Hypothesis requires Evidence to be scientifically meaningful) is stronger than the implementation dependency. Building them together ensures no hypothesis exists without evidence support, even during the initial implementation phase. The merge adds zero additional code — both objects were going to be built anyway.

**Expected Benefits:** Cleaner conceptual model. No orphan hypotheses. Faster time to scientific usefulness.

**Known Trade-offs:** Slightly larger initial implementation surface. The existing pipeline integration milestones (linking hypotheses to decisions, outcomes) are deferred to later iterations regardless.

**Conditions for Future Re-evaluation:** None. The merge is permanent. If future evidence shows that separating them provides benefits, a split would only be warranted if the combined implementation becomes unmanageable.

**Status:** ACCEPTED

---

## Decision ID-002: 4-State Hypothesis Lifecycle (Reduced from 7)

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** The Hypothesis lifecycle uses 4 states (FORMULATED → ACTIVE → EVALUATED → ARCHIVED) instead of the 7 states defined in 02_SCIENTIFIC_OBJECT_MODEL.md §6.1 (CANDIDATE → FORMULATED → ACTIVE → EVALUATED → CONFIRMED/REJECTED/INCONCLUSIVE → ARCHIVED).

**Context:** The object model defined a 7-state lifecycle. The Implementation Bridge self-review (S-06) recommended: "Even 7 states may be too many for the first implementation. Consider starting with 4 states: FORMULATED → ACTIVE → EVALUATED → ARCHIVED." The three terminal verdict states (CONFIRMED, REJECTED, INCONCLUSIVE) are collapsed into EVALUATED. The CANDIDATE state is eliminated.

**Alternatives Considered:**
- **7 states (object model):** Full fidelity. Risk: state machine complexity with 21+ transition rules. The first iteration would spend more time on state management than on scientific value.
- **4 states (chosen):** FORMULATED → ACTIVE → EVALUATED → ARCHIVED. Terminal verdicts become attributes (e.g., `verdict` field on EVALUATED hypothesis), not separate states.
- **3 states (even simpler):** FORMULATED → ACTIVE → ARCHIVED. Risk: losing the EVALUATED state eliminates the distinction between "currently being tracked" and "outcome observed."

**Evidence:** The Implementation Bridge S-06 explicitly recommended the 4-state reduction. No evidence yet suggests finer state granularity is required for scientific traceability.

**Reasoning:**
- CANDIDATE is an organizational state, not a scientific one. Ideas that may become hypotheses are not hypotheses. The system should not store non-hypotheses.
- CONFIRMED/REJECTED/INCONCLUSIVE are verdicts, not lifecycle stages. A hypothesis is EVALUATED when the outcome is observed; the verdict is data attached to that evaluation, not a separate state requiring its own transition rules.
- The 4-state model reduces transition rules from ~10 to 5, each clearly defined. Simpler to verify, simpler to test, simpler to maintain.

**Expected Benefits:** Lower cognitive load. Fewer edge cases. Easier to verify correctness. Faster to implement.

**Known Trade-offs:** The terminal verdict is not a first-class state. Queries like "find all confirmed hypotheses" require filtering EVALUATED hypotheses by a `verdict` attribute rather than querying a CONFIRMED state. This is a minor query overhead with no scientific loss.

**Conditions for Future Re-evaluation:** If analysis shows that the CONFIRMED/REJECTED/INCONCLUSIVE distinction requires separate state transitions (e.g., different archiving rules per verdict), the states should be restored. This would be a database migration adding two intermediate states — low risk.

**Status:** ACCEPTED

---

## Decision ID-003: Separate Scientific Database

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** Scientific records (hypotheses, evidence) are stored in a separate SQLite database (`scientific.db`) rather than extending the existing operational database (`oma_core.db`).

**Context:** The existing MVP uses `oma_core.db` with tables for events, opportunities, and user profiles. The Implementation Bridge identified the risk of "impedance mismatch between objects and relational tables" (Risk 8.3) and recommended "Hypothesis tables can be dropped without affecting events/trades" as a rollback condition (Condition 5).

**Alternatives Considered:**
- **Single database (oma_core.db extension):** Add hypothesis and evidence tables to the existing database. Simpler deployment (one file). Risk: scientific data entangled with operational data. Rollback requires migration scripts. Query performance degraded by unrelated table growth.
- **Separate database (chosen):** Isolated `scientific.db`. Independent lifecycle. Zero impact on operational queries. Rollback = delete file.
- **Document store (JSONL directory):** Each hypothesis and evidence as JSONL files. Lowest coupling. Risk: no query capability, no relational integrity, harder to evolve schema.

**Evidence:** The Implementation Bridge (Risk 8.3) identified the impedance mismatch risk explicitly. The Condition 5 rollback requirement ("Hypothesis tables can be dropped without affecting events/trades") is trivially satisfied with a separate database.

**Reasoning:**
- The operational database and scientific database have fundamentally different query patterns, mutability requirements, and evolution speeds. Mixing them creates coupling that benefits neither.
- A separate database provides complete isolation. The operational MVP continues running even if the scientific database is corrupted, deleted, or migrated to a different technology.
- The cost (one additional file handle, slightly more complex initialization) is negligible.

**Expected Benefits:** Zero regression risk. Independent schema evolution. Independent backup/restore. Trivial rollback. Clear separation of concerns.

**Known Trade-offs:** Two database connections instead of one. Slightly more complex deployment (two files to manage). Cross-database queries (e.g., "find all trades linked to this hypothesis") require application-level joins rather than SQL joins.

**Conditions for Future Re-evaluation:** When cross-database queries become a performance bottleneck, consider: (a) adding hypothesis_id to operational tables (denormalization), or (b) merging databases with careful migration. Neither is warranted until Iteration 3 (Outcome Comparison) or later.

**Status:** ACCEPTED

---

## Decision ID-004: Scientific Layer as New Package

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** All scientific objects and logic live in a new `core/scientific/` package rather than being distributed across existing modules.

**Context:** The existing codebase has established packages: `schemas/`, `database/`, `execution/`, `council/`, etc. The Implementation Bridge (Part X) states: "Code follows objects. The structure of the code reflects the structure of the object model. Hypothesis has a file (or module) because it is a first-class object."

**Alternatives Considered:**
- **Distributed across existing packages:** Hypothesis schema in `schemas/`, lifecycle in a new module, storage in `database/`. Risk: scientific concepts scattered across operational packages, unclear boundaries.
- **New package (chosen):** `core/scientific/` contains all scientific objects. Clear boundary. Easy to find. Easy to replace independently.

**Evidence:** The Implementation Bridge §10.1 ("Code follows objects") provides the architectural principle. No evidence favors distribution.

**Reasoning:**
- Scientific objects have a different purpose, lifecycle, and evolution path than operational objects. They belong together.
- A single package makes it obvious where scientific code lives. Future contributors do not need to guess.
- The package boundary enforces separation of concerns. Scientific code cannot accidentally import operational internals.

**Expected Benefits:** Discoverability. Maintainability. Enforced separation of concerns.

**Known Trade-offs:** Schemas are split across `schemas/` (operational) and `scientific/` (scientific). However, Hypothesis and Evidence schemas remain in `schemas/` per convention — only lifecycle and storage logic are in the new package.

**Conditions for Future Re-evaluation:** If the scientific layer grows beyond ~15 files, consider sub-packages (`scientific/lifecycle/`, `scientific/storage/`, `scientific/analysis/`). Not warranted yet.

**Status:** ACCEPTED

---

## Decision ID-005: Manual Hypothesis Creation (CLI-Based)

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** Hypotheses are created manually via CLI commands rather than by automated system processes.

**Context:** The Implementation Bridge self-review (S-07 Item 1) asked: "Should the first Hypothesis be created by the system or by a human? Start with human-created hypotheses to establish quality. Add system-generated hypotheses when the formation mechanism is validated."

**Alternatives Considered:**
- **Automated creation:** Agents generate hypotheses from events. Risk: low-quality hypotheses before validation, no quality baseline.
- **Manual creation (chosen):** Human creates hypotheses via CLI. Quality controlled. Establishes baseline for what a good hypothesis looks like.
- **Hybrid:** Manual + automated with quality gate. Risk: complexity not justified for Iteration 1. Postponed.

**Evidence:** No prior data exists on hypothesis quality in this system. Automated generation without a quality baseline would produce unmeasurable results.

**Reasoning:** The project has zero experience generating hypotheses. Manual creation establishes: (a) what fields are needed in practice, (b) what constitutes a well-formed hypothesis, (c) the baseline quality level. Automated generation will be added in a future iteration after sufficient examples exist to learn from.

**Expected Benefits:** Quality control. Baseline establishment. No speculative automation code.

**Known Trade-offs:** Low hypothesis volume initially. Human bottleneck. Not scalable to hundreds of hypotheses per day.

**Conditions for Future Re-evaluation:** When the system has ≥50 manually created hypotheses, automated hypothesis formation becomes implementable. Criteria: hypothesis quality metrics show consistent patterns, and the manual bottleneck limits research velocity.

**Status:** ACCEPTED

---

## Decision ID-006: DecisionRecord Deferred

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** DecisionRecord is not implemented. It will be introduced in a later iteration (originally Iteration 5, simplified roadmap).

**Context:** The object model defines DecisionRecord as the primary aggregate bundling Hypothesis, Evidence, Decision, Outcome, Reflection, Knowledge for one operational cycle. The Implementation Bridge simplified roadmap (S-04) defers DecisionRecord to Iteration 4. Since Hypothesis and Evidence are Iteration 1, and Decision, Outcome, Knowledge do not yet exist, DecisionRecord cannot be implemented.

**Alternatives Considered:**
- **Implement empty DecisionRecord:** Create the schema with only hypothesis_id populated. Risk: speculative schema. Would be mostly NULL fields. Pre-mature.
- **Defer (chosen):** DecisionRecord will be implemented when Decision, Outcome, and Knowledge exist to populate it.

**Evidence:** The Implementation Bridge (S-02) accepted "DecisionRecord can be a query view rather than a stored entity for initial implementation." Since none of its constituent objects (except Hypothesis and Evidence) exist, there is nothing to aggregate.

**Reasoning:** Implementing an aggregate before its constituents exist is building storage for data that does not exist. This violates Invariant 7 (Minimal Complexity) and Invariant 1 (Evidence First — there is no evidence that the aggregate schema is correct).

**Expected Benefits:** No speculative code. Clean implementation sequence.

**Known Trade-offs:** The transition from isolated objects to aggregate DecisionRecord will require integration work in a later iteration. The aggregate schema may need adjustment based on experience with the individual objects.

**Conditions for Future Re-evaluation:** When Decision, Outcome, Knowledge, and Reflection are all implemented (Iterations 2–5), DecisionRecord becomes implementable.

**Status:** ACCEPTED

---

## Decision ID-007: ResearchProposal Deferred

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** ResearchProposal is not implemented. It will be deferred past the initial six iterations.

**Context:** The object model defines ResearchProposal as the grouping mechanism for experiments. The Implementation Bridge self-review (S-04) deferred it entirely: "ResearchProposal is deferred past the initial eight iterations. The system can generate hypotheses without formal proposals."

**Alternatives Considered:**
- **Implement ResearchProposal:** Full object with lifecycle. Risk: overhead without benefit until hypotheses produce knowledge that needs grouping.
- **Default "Exploratory" proposal:** Lightweight placeholder. Risk: becomes a dumping ground, defeating the purpose.
- **Defer entirely (chosen):** No ResearchProposal code. Hypotheses exist independently until the need for grouping emerges from evidence.

**Evidence:** The Implementation Bridge S-04 explicitly deferred ResearchProposal. No operational need exists yet to group hypotheses under formal research questions. The first hypotheses are manual and exploratory — they do not belong to a formal research program.

**Reasoning:** ResearchProposal is scientifically valuable but operationally premature. Adding it now would create a schema that is populated with a single "General Research" proposal containing all hypotheses — which provides no analytical benefit over having no proposal at all. The structure is justified only when criterion gaps are specific enough to warrant targeted investigation.

**Expected Benefits:** Less code. Less conceptual overhead. More flexibility in early hypothesis formation.

**Known Trade-offs:** Adding ResearchProposal later requires migrating existing hypotheses into proposals. Migration is straightforward: add a `proposal_id` column to hypotheses (nullable), with a default "General Research" proposal for existing records.

**Conditions for Future Re-evaluation:** When CriterionSnapshot (Iteration 6) identifies specific criterion gaps that warrant targeted investigation. Alternatively, when the number of hypotheses exceeds 50 and informal grouping becomes insufficient for analysis.

**Status:** ACCEPTED

---

## Decision ID-008: Evidence Source as Free Text

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** Evidence source is recorded as a free-text string (`source_id`) rather than a structured enum of source categories.

**Context:** The Evidence object (02_SCIENTIFIC_OBJECT_MODEL.md Object 2) requires "Identify its source with reliability metadata." The source is an attribute, not an independent object. The question of structured categorization vs. free-text was left open.

**Alternatives Considered:**
- **Structured enum (e.g., MARKET, NEWS, MACRO, ONCHAIN, etc.):** Enables filtering and analysis by source category. Risk: enum must be maintained as new source types emerge. Creates premature taxonomy.
- **Free text (chosen):** `source_id` as string. Any source name is valid. Enables ad-hoc categorization later via string matching.
- **Both:** Free text + optional category enum. Risk: dual representation, ambiguous which to use.

**Evidence:** No evidence yet demonstrates that analysis by source category requires structured support. The existing `evidence` table with `source_id` enables filtering by exact source name, which is sufficient for current query needs.

**Reasoning:** Free text is the simplest representation that satisfies the object model requirement ("Identify its source"). A structured enum would be speculative — we do not know what source categories will be most useful because we have not yet collected enough evidence to analyze. Free text defers categorization to the analysis layer, where it belongs.

**Expected Benefits:** Simpler schema. No enum maintenance. Maximum flexibility for source naming.

**Known Trade-offs:** Querying by source category requires string matching or tagging conventions rather than direct enum filtering. Analysis queries that group evidence by source type must define the grouping logic in application code rather than the database.

**Conditions for Future Re-evaluation:** When evidence volume exceeds 1,000 items AND analysis shows that source category queries are a bottleneck, add an optional `source_category` column. Migration: `ALTER TABLE evidence ADD COLUMN source_category TEXT`. Existing evidence will have NULL category.

**Status:** ACCEPTED

---

## Decision ID-009: Question Not Added to Hypothesis

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** The `question_id` field is NOT added to the Hypothesis schema. The link between hypotheses and research questions will flow through ResearchProposal when it is implemented.

**Context:** The object model disposes Question as an ATTRIBUTE of ResearchProposal (Section 2.3: "Question is a property of what is being investigated"). The relationship chain is: Hypothesis → ResearchProposal → Question. Adding `question_id` to Hypothesis would create a direct link that bypasses ResearchProposal and denormalizes the object model.

**Alternatives Considered:**
- **Add question_id to Hypothesis:** Direct query path. Risk: bypasses ResearchProposal, denormalizes the model, creates anticipation of future functionality.
- **Defer (chosen):** Link will flow through ResearchProposal when implemented.

**Evidence:** The object model explicitly disposes Question as ATTRIBUTE of ResearchProposal (Section 2.3). Adding `question_id` to Hypothesis would contradict this disposition.

**Reasoning:**
- The object model defines Question as an attribute of ResearchProposal, not Hypothesis. Adding it to Hypothesis would mean a concept that was intentionally demoted to ATTRIBUTE would become a cross-cutting foreign key — elevating its significance.
- The traceability chain "hypothesis → research question" is important but not urgent. No hypothesis has yet been linked to a formal research question because no ResearchProposal exists.
- Adding `question_id` now would result in NULL values for all existing hypotheses — dead weight in every record.

**Expected Benefits:** Preserves object model integrity. No speculative fields. No NULL columns.

**Known Trade-offs:** When ResearchProposal is implemented, adding the hypothesis → proposal link requires populating the new column from existing data if a retrofit is needed. Migration: add `proposal_id` to hypotheses table, nullable, with a default "General Research" proposal.

**Conditions for Future Re-evaluation:** When ResearchProposal is implemented (deferred — see ID-007). At that point, evaluate whether a direct question_id shortcut on Hypothesis provides analytical value beyond the ResearchProposal chain.

**Status:** ACCEPTED

---

## Decision ID-010: Weight and Reliability Clamping at Store Layer

- **Date:** June 2026
- **Iteration:** 1
- **Decision:** Evidence weight and source reliability values are clamped to [0.0, 1.0] in the ScientificStore's `add_evidence()` method, not in the Evidence dataclass itself.

**Context:** The Evidence schema defines `weight`, `source_reliability`, and `independence_score` as floats without range constraints. The object model implies [0,1] ranges but does not specify enforcement location.

**Alternatives Considered:**
- **Clamp in dataclass (`__post_init__`):** Enforces constraint at construction time. Risk: hides input errors. Silent correction.
- **Clamp in store layer (chosen):** Enforces constraint at persistence time. The dataclass allows any float; the store clamps to valid range.
- **No clamping (validation only):** Raise error on out-of-range input. Risk: breaks CLI flow, forces error handling everywhere.

**Evidence:** Weight, reliability, and independence are inherently bounded [0,1] in the scientific model. Values outside this range are meaningless but do not damage data integrity — they simply indicate an error in the input pipeline.

**Reasoning:**
- The store layer is the boundary between internal and external data. Clamping at this boundary ensures persistence always contains valid values while keeping the dataclass pure (no side effects in `__post_init__`).
- Silent clamping at the store layer is intentional: extreme inputs (1.5, -0.3) are input errors, not scientific data. Clamping to [0,1] preserves the input's intent while maintaining data integrity.
- The dataclass remains a "dumb container" — it does not enforce business rules. This is consistent with the existing MVP pattern (Event, AgentOpinion, Trade schemas do not enforce domain constraints).

**Expected Benefits:** Pure dataclasses. Clear enforcement boundary. No surprise validation in schema code.

**Known Trade-offs:** Silent correction of invalid input may hide upstream bugs. If this becomes a problem, add a warning log when clamping occurs.

**Conditions for Future Re-evaluation:** If evidence quality analysis shows that clamped values are systematically distorting weight distributions, move enforcement to the dataclass or add input validation that warns/rejects.

**Status:** ACCEPTED

---

## Decision ID-011: Evidence Independence Score Default

- **Date:** June 2026
- **Iteration:** 1 (corrected in 1.1)
- **Decision:** The `independence_score` on Evidence defaults to 0.5 in the application layer. The SQL table schema default was corrected from 1.0 to 0.5 during Iteration 1.1 refinement.

**Context:** The Evidence object model (02_SCIENTIFIC_OBJECT_MODEL.md Object 2) requires "Record its independence from other evidence items." No prior data exists on evidence independence in this system. The initial implementation had a mismatch: Python default 0.5, SQL default 1.0.

**Alternatives Considered:**
- **1.0 (fully independent):** Assumes all evidence is independent until proven otherwise. Risk: overconfident evidence quality scores. Creates false sense of diverse evidence.
- **0.5 (unknown/medium) — chosen:** Assumes unknown independence. Neutral starting point. Any future refinement will move the score either up or down.
- **0.0 (fully dependent):** Assumes all evidence may be redundant. Risk: underweighting genuinely independent evidence.

**Evidence:** No data exists on evidence independence patterns. The default is a placeholder refined through evidence collection.

**Reasoning:** 0.5 represents "unknown" — the most honest default. It makes no assumption about independence. It biases analysis toward underweighting evidence rather than overweighting it, which is the safer scientific choice. The SQL default was corrected to match the application default, eliminating the inconsistency.

**Expected Benefits:** Honest baseline. Conservative weighting. Consistent defaults across layers.

**Known Trade-offs:** Early analyses may show lower evidence diversity scores than if 1.0 were used. This is correct — the system should not assume independence without evidence.

**Conditions for Future Re-evaluation:** When 100+ evidence items exist, compute actual independence distribution. If mean differs significantly from 0.5, adjust the default.

**Status:** ACCEPTED (SQL default corrected in Iteration 1.1)

---

## Decision ID-012: Metadata Field Removed from Hypothesis and Evidence

- **Date:** June 2026
- **Iteration:** 1.1 (Refinement)
- **Decision:** The `metadata: Dict[str, Any]` field was removed from both Hypothesis and Evidence dataclass definitions, serialization methods, SQL schemas, and store layer.

**Context:** The initial implementation included a `metadata` dict as a catch-all for future extensibility. During the Iteration 1.1 scientific review, it was identified as speculative — nothing stores data in it, and no requirement justifies its existence.

**Alternatives Considered:**
- **Keep metadata:** Maintain the field "just in case." Violates Invariant 7 (Minimal Complexity) — the field cannot justify its existence. Every serialization/deserialization path must handle it.
- **Remove metadata (chosen):** Eliminate the field entirely. Future extensibility will be added via specific fields or ALTER TABLE, justified by evidence.
- **Replace with typed optional fields:** Only add fields with documented requirements. None exist.

**Evidence:** Zero evidence items stored in metadata across all test data. Zero requirements in the object model or implementation bridge requiring a catch-all metadata field. The burden of proof is on complexity (Invariant 7), and no proof was provided.

**Reasoning:** Rule 9 of the Research Protocol requires every complexity addition to justify its existence. The metadata field failed — it was added speculatively, not in response to evidence. Removal eliminates code paths in to_dict, from_dict, SQL INSERT, UPDATE, JSON serialization, and test assertions without reducing scientific capability.

**Expected Benefits:** Reduced schema surface area. Fewer serialization paths. Less code. Clearer boundaries.

**Known Trade-offs:** Future field additions require schema migration. This is standard practice with minimal risk given the isolated scientific database (ID-003).

**Conditions for Future Re-evaluation:** If evidence demonstrates that catch-all extensibility is needed, the field can be restored. Migration: `ALTER TABLE hypotheses ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'`.

**Status:** ACCEPTED (applied in Iteration 1.1)

---

## Decision ID-013: Evidence Source Category Not Implemented

- **Date:** June 2026
- **Iteration:** 1 (reaffirmed in 1.1)
- **Decision:** Evidence source is recorded as free-text `source_id` only. No structured `source_category` enum is implemented.

**Context:** Scientific review question: should Evidence carry a structured source category (Market, News, Macro, On-chain, Experiment, Backtest, Paper Trading, Manual Observation) to enable analysis by source type?

**Alternatives Considered:**
- **Add source_category enum:** Structured categorization enables filtering and aggregation by source type. Risk: premature taxonomy that may not match actual evidence sources.
- **Free text only (chosen):** source_id is sufficient for identification. Category analysis can be done via application-level string matching.
- **Optional nullable enum:** Both free text and optional category. Risk: dual representation creates ambiguity.

**Evidence:** Zero evidence exists to validate a source category taxonomy. The need for source-type analysis is a future requirement, not a present one. The object model requires "Identify its source with reliability metadata" — source_id satisfies this.

**Reasoning:** Adding a structured category enum before any evidence exists to validate the taxonomy is speculative engineering. Correct categories cannot be known until evidence is collected and analyzed. Free text preserves flexibility; structured categories can be added when the need is demonstrated.

**Expected Benefits:** Simpler schema. No premature taxonomy. Maximum naming flexibility.

**Known Trade-offs:** Queries filtering by source category require string matching. Acceptable until evidence volume makes it a bottleneck.

**Conditions for Future Re-evaluation:** When evidence exceeds 1,000 items AND analysis shows source category queries would improve capability, add optional `source_category TEXT`. Migration: `ALTER TABLE evidence ADD COLUMN source_category TEXT`.

**Status:** ACCEPTED

---

## Decision ID-014: Hypothesis-to-Question Link Deferred Through ResearchProposal

- **Date:** June 2026
- **Iteration:** 1 (reaffirmed in 1.1)
- **Decision:** No `question_id` field is added to Hypothesis. The link between hypotheses and research questions will flow through ResearchProposal when implemented.

**Context:** Scientific review question: should Hypothesis carry a `question_id` for traceability to the research question it tests?

**Object Model Reference:** Question is dispositioned as ATTRIBUTE of ResearchProposal (02_SCIENTIFIC_OBJECT_MODEL.md §2.3, item 2). Relationship chain: Hypothesis → ResearchProposal → Question. Adding `question_id` to Hypothesis would denormalize this.

**Alternatives Considered:**
- **Add question_id to Hypothesis:** Direct traceability. Risk: denormalizes object model, all existing hypotheses get NULL question_id, creates anticipation of future functionality.
- **Defer through ResearchProposal (chosen):** When ResearchProposal is implemented, add `proposal_id` to Hypothesis. Question accessed through the proposal.
- **Add nullable question_id now:** Same risks as direct addition, with additional cost of maintaining an unpopulated field.

**Evidence:** The object model is explicit. No evidence suggests this disposition is incorrect. No hypothesis has been linked to a formal research question.

**Reasoning:** Adding question_id to Hypothesis would elevate a concept intentionally demoted to ATTRIBUTE into a cross-cutting foreign key — contradicting the object model. The proper traceability chain preserves conceptual integrity. The indirect link (Hypothesis → proposal_id → ResearchProposal → Question) is sufficient.

**Expected Benefits:** Object model integrity preserved. No speculative fields. No NULL columns.

**Known Trade-offs:** Queries like "all hypotheses for question X" require a join through ResearchProposal. Minor cost for significant conceptual clarity.

**Conditions for Future Re-evaluation:** When ResearchProposal is implemented, evaluate whether the indirect link is sufficient. If direct query performance is critical, a denormalized question_id can be added with evidence to justify it.

**Status:** ACCEPTED

---

## ERA II Iteration 1 — Readiness Review

**Date:** June 2026
**Review Type:** Scientific refinement (Iteration 1.1)
**Verdict:** **PASS**

### Dimension Evaluation

| Dimension | Verdict | Evidence |
|-----------|---------|----------|
| **Scientific Completeness** | ✅ PASS | All 7 success criteria met. Hypothesis has 4-state lifecycle. Evidence has direction, weight, source_id, lifecycle. Evidence hypothesis binding enforced. |
| **Architectural Consistency** | ✅ PASS | Object model followed (§2.3 dispositions respected). ResearchProposal deferred per S-04. DecisionRecord deferred. 8 invariants preserved. |
| **Implementation Discipline** | ✅ PASS | No future-iteration functionality. No premature abstractions. Speculative metadata field identified and removed during review. |
| **Future Extensibility** | ✅ PASS | Clean separation enables Iterations 2–6. Decision/Outcome/Knowledge integration points are additive, not refactoring. |
| **Minimal Complexity** | ✅ PASS | 4 states (not 7). 6 required Hypothesis fields. Free-text source (not enum). No empty aggregate schemas. No speculative fields remaining. |
| **Backward Compatibility** | ✅ PASS | 303 tests pass. Zero existing operational code modified for functionality. oma_core.db untouched. All existing CLI commands unchanged. |

### Refinements Applied During Review

1. **ID-012: Removed speculative metadata field** from Hypothesis and Evidence schemas, serialization, SQL, and store layer.
2. **ID-011: Corrected SQL default** for independence_score from 1.0 to 0.5 to match application layer.
3. All refinements verified: 23/23 scientific layer tests pass. 303/303 total tests pass.

### Conditions for Iteration 2

**Iteration 1 is complete.** The system can:
- Create hypotheses with all required fields
- Transition hypotheses through full lifecycle (FORMULATED → ACTIVE → EVALUATED → ARCHIVED)
- Attach supporting and contradicting evidence to any hypothesis
- Activate, expire, and supersede evidence independently
- Query by status, hypothesis_id, direction

**Iteration 2 (Hypothesis-Linked Decisions) may begin when ready.**
