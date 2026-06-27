# Implement Now — Green-Lane Ideas

*Version 1.0 — June 2026*
*Lane: GREEN — Safe to implement on USB*

---

## Important Notice

None of the following ideas are implemented unless explicitly confirmed by repository evidence. This document recommends implementation priorities — it does not describe existing functionality.

If an idea appears here and also exists in the codebase, the codebase is the source of truth. This document describes what should be built next, not what already exists.

---

## Green-Lane Criteria

- Additive — does not modify existing operational code
- Low risk — cannot destabilize the operational MVP
- Observability, documentation, analytics, or reports
- Does not touch execution, agents, council, collectors, or databases
- Can be implemented on USB independently
- Improves at least one scarce resource
- Validatable with existing test infrastructure

---

## Green-Lane Ideas

---

### 1. Missed Opportunity Ledger

**Problem solved:** The system currently tracks only the opportunities it acted on. It has no record of opportunities it evaluated and rejected, opportunities it missed while another was processing, or opportunities it ignored because of capacity limits. This creates selection bias in every performance metric — the system cannot know whether its rejections were correct.

**Why now:** Without this ledger, all performance analysis is fundamentally biased. The system cannot learn from decisions not to act. This is the most significant blind spot in the current observability architecture.

**Expected impact:** Complete decision traceability. The system can answer: "How many opportunities did we evaluate? How many did we act on? How many did we reject? Were our rejections correct?"

**Scarce resources improved:** Knowledge (understanding of decision quality), Capital (better allocation through better rejection data)

**Complexity:** Low

**Risk:** Very low — additive observability, no execution path impact

**Validation method:** Unit tests verifying ledger creation, querying, and aggregation. Integration test showing ledgers track rejected and ignored opportunities.

**Implementation boundary:** New module (`core/innovation/missed_opportunity_ledger.py` or similar), independent of all existing operational code. Lightweight SQLite table or JSONL append log.

**What it must NOT touch:** Trade execution, Council decisions, agent opinions, collectors, event bus, `oma_core.db`

**Dependencies:** None

**Verdict:** IMPLEMENT NOW

---

### 2. Opportunity Uniqueness Score

**Problem solved:** The system currently treats every opportunity as equally valuable at the moment it is evaluated. There is no concept of how rare or replaceable an opportunity is. This makes it impossible to prioritize when multiple opportunities compete for limited capital or attention.

**Why now:** Without uniqueness scoring, the system cannot allocate scarce resources to the most valuable opportunities. This is a prerequisite for any future resource allocation intelligence.

**Expected impact:** The system can distinguish "this opportunity appears once a month" from "this opportunity appears every hour." Rare opportunities receive higher priority.

**Scarce resources improved:** Capital, Time, Attention (better triage)

**Complexity:** Low-Medium

**Risk:** Low — analytics only, does not affect execution

**Validation method:** Unit tests on scoring logic. Historical analysis on recorded opportunities to verify scores are meaningful.

**Implementation boundary:** Scoring function that runs on opportunity data. No changes to execution path.

**What it must NOT touch:** Trade execution, Council, agents, collectors

**Dependencies:** Missed Opportunity Ledger (P2-1) provides the data needed to compute baselines

**Verdict:** IMPLEMENT NOW

---

### 3. Auto-Approval Readiness Score

**Problem solved:** When the system reaches Level 2 autonomy (auto-execute with approval), it needs a score indicating whether a specific hypothesis-decision pair is safe to auto-approve. This score must be evidence-based — it must reflect past performance of similar decisions, confidence calibration, and risk assessment.

**Why now:** The score itself does not require an Approval Engine. It can be designed, tested, and validated independently. When the Approval Engine is built, the scoring function will already exist.

**Expected impact:** Readiness score becomes the gate for Level 2 autonomy. No auto-approval happens without a sufficient readiness score.

**Scarce resources improved:** Capital (prevents premature execution), Attention (reduces manual review burden for safe decisions)

**Complexity:** Medium

**Risk:** Low — design and simulation only, no execution integration

**Validation method:** Simulate scores on historical decisions. Verify that high-scoring decisions had better outcomes. Adjust scoring weights based on evidence.

**Implementation boundary:** Pure function computing readiness from hypothesis quality, evidence strength, confidence calibration, and risk context.

**What it must NOT touch:** Trade execution, Council, agents, any code that makes or executes decisions

**Dependencies:** Missed Opportunity Ledger (P2-1), Opportunity Uniqueness Score (P2-2), eventual Approval Engine

**Verdict:** IMPLEMENT NOW

---

### 4. Opportunity Cost Report

**Problem solved:** When the system chooses one opportunity over another, there is no record of what was sacrificed. Over time, the system cannot answer: "What was the cost of choosing A over B?"

**Why now:** Opportunity cost is the core concept of resource allocation. Without measuring it, the system cannot improve its allocation decisions.

**Expected impact:** Every decision can be evaluated not just on its own outcome, but on the outcome of the next-best alternative that was rejected.

**Scarce resources improved:** Capital, Knowledge (understanding trade-offs)

**Complexity:** Medium

**Risk:** Low — analytical, does not affect execution

**Validation method:** Generate reports on historical data. Verify opportunity cost calculations are correct and useful.

**Implementation boundary:** Report generation module. Works on ledger data.

**What it must NOT touch:** Trade execution, decision-making code

**Dependencies:** Missed Opportunity Ledger (P2-1) — without rejected opportunity data, opportunity cost cannot be computed

**Verdict:** IMPLEMENT NOW

---

### 5. Signal-to-Decision Audit

**Problem solved:** There is currently no end-to-end traceability from raw signal through hypothesis to decision. When a decision is evaluated, it is difficult to reconstruct what signals contributed to it.

**Why now:** Traceability is an architecture invariant (Invariant 4). An audit trail from signal to decision is required before any autonomy increase.

**Expected impact:** Every decision can be traced back through its entire chain: signal → event → reasoning → hypothesis → evidence → decision. This enables quality analysis at every step.

**Scarce resources improved:** Knowledge (understanding decision quality)

**Complexity:** Medium

**Risk:** Low — traceability is additive and read-only

**Validation method:** Unit tests verifying that signals, hypotheses, and decisions can be linked. Integration test for a complete trace.

**Implementation boundary:** New audit data structure linking signal IDs through the pipeline. Read-only — does not change any existing component.

**What it must NOT touch:** Trade execution, Council, agents, collectors, event bus processing logic

**Dependencies:** None directly, but richer with Missed Opportunity Ledger

**Verdict:** IMPLEMENT NOW

---

### 6. Notification Quality Gate

**Problem solved:** The system currently sends notifications for every significant event. There is no mechanism to prevent notification overload, no budget for the user's attention, no priority tiers.

**Why now:** Attention is the most scarce resource. Every notification consumes it. Without a quality gate, the system will eventually overwhelm the user — making all notifications noise.

**Expected impact:** The user receives notifications proportional to their importance. Low-importance signals are batched or suppressed. The user's attention is protected.

**Scarce resources improved:** Attention (primary), Time (secondary)

**Complexity:** Low

**Risk:** Very low — only affects notification output, not system operation

**Validation method:** Unit tests on notification priority logic. Manual verification that high-priority notifications pass through while low-priority ones are suppressed or batched.

**Implementation boundary:** Notification filter/suppressor module that sits between the system and Telegram/CLI output.

**What it must NOT touch:** Trade execution, Council, agents, collectors, any decision-making code

**Dependencies:** None

**Verdict:** IMPLEMENT NOW

---

### 7. Terminal Cockpit Evolution

**Problem solved:** The current CLI (`core/cli/main.py`) provides operational commands but limited scientific visibility. The cockpit (laptop version) aggregates system state but does not expose hypothesis quality, evidence trends, or Criterion signals.

**Why now:** The terminal is the primary interface. Improving it has zero operational risk and immediate value for the one-person founder.

**Expected impact:** The user can monitor not just system health but also scientific health — hypothesis status, evidence accumulation, learning velocity.

**Scarce resources improved:** Attention, Time (better situational awareness in less time)

**Complexity:** Medium

**Risk:** Low — CLI changes are additive and do not affect underlying logic

**Validation method:** Manual testing. Verify new commands produce correct output.

**Implementation boundary:** New CLI commands and display formatting only. No changes to underlying modules.

**What it must NOT touch:** Trade execution, Council, agents, collectors, databases

**Dependencies:** Scientific Store (already exists) — cockpit can read hypothesis and evidence stats

**Verdict:** IMPLEMENT NOW

---

## Summary

| # | Idea | Priority | Complexity | Risk | Dependencies |
|---|------|----------|------------|------|--------------|
| 1 | Missed Opportunity Ledger | Highest | Low | Very low | None |
| 2 | Opportunity Uniqueness Score | High | Low-Medium | Low | Ledger |
| 3 | Auto-Approval Readiness Score | High | Medium | Low | Ledger, Uniqueness |
| 4 | Opportunity Cost Report | Medium | Medium | Low | Ledger |
| 5 | Signal-to-Decision Audit | High | Medium | Low | None |
| 6 | Notification Quality Gate | High | Low | Very low | None |
| 7 | Terminal Cockpit Evolution | Medium | Medium | Low | Scientific Store |

**Recommended implementation order:** 1 → 6 → 5 → 2 → 3 → 4 → 7

---
