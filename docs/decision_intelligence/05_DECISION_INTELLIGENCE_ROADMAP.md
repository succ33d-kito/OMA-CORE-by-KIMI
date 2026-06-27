# Decision Intelligence Roadmap

## O.M.A.-C.O.R.E. Decision Intelligence — Component 5

*Version 1.0 — June 2026*

---

## 1. Purpose

This roadmap defines the stages from the current state (Stage 8 complete) to autonomous approval capability. It is not a calendar — it is a dependency-driven progression where each stage unlocks the next. No stage can be skipped. Validation gates must be passed before the next stage begins.

---

## 2. Current State Assessment

| Dimension | Current Maturity | Target for Autonomous Approval |
|---|---|---|
| **Schemas** | Complete (Hypothesis, Evidence, OutcomeComparison, Knowledge, CriterionDelta) | Complete |
| **Scientific Lab** | Complete (comparison, lifecycle, evolution, store) | Complete |
| **Historical Replay** | Complete (engine, CLI, 10-trade fixture, 55 tests) | Needs ≥1000 replayed trades |
| **Decision Confidence Engine** | Not implemented | Designed, needs implementation |
| **Approval Engine** | Not implemented | Designed, needs implementation |
| **Scarce Resources Model** | Defined | Implemented as measurement layer |
| **Decision Policy** | Defined | Implemented as configuration layer |
| **Operational Integration** | Lab runs on fixtures only | Live read-only source access |
| **Paper Trading Feedback** | Paper trading runs independently | Paper trading feeds confidence calibration |
| **Real Capital Readiness** | Not ready | Requires minimum maturity across all dimensions |
| **Autonomy** | Stage 0 (human-only, de facto) | Stage 5 (full autonomy, target) |

---

## 3. Roadmap Stages

---

### Stage 9 — Read-Only Operational Integration

**Objective**: Connect the lab to real operational data sources without write access.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 9.1 Define read-only source interface | Stage 8 complete | 1 day |
| 9.2 Implement SQLite source reader for oma_core.db | Stage 9.1 | 2 days |
| 9.3 Implement JSON/JSONL reader for paper trading logs | Stage 9.1 | 1 day |
| 9.4 Source authentication with read-only tokens | Stage 9.1 | 1 day |
| 9.5 Data freshness monitoring | Stage 9.2, 9.3 | 1 day |
| 9.6 Source health checks (connectivity, format validation) | Stage 9.2, 9.3 | 1 day |
| 9.7 Integration tests with real (anonymized) data samples | Stage 9.2–9.6 | 2 days |

**Validation Gate**: 100+ real historical trades from operational sources processed in dry-run mode through the full lab pipeline. Zero write attempts to operational sources. All source connection failures handled gracefully.

**Risk**: Operational schema drift between development and production environments.

**GO / NO GO Checkpoint**: Pass → Stage 10. Fail → Return to Stage 9 and resolve schema mismatch.

---

### Stage 10 — Confidence Engine Implementation

**Objective**: Implement the Decision Confidence Engine as a pure Python module.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 10.1 Implement sub-dimension computation functions (12 functions) | Stage 9 | 3 days |
| 10.2 Implement confidence vector aggregation (policy-governed) | Stage 10.1 | 2 days |
| 10.3 Implement calibration computation (Brier score, bias, resolution) | Stage 10.1 | 2 days |
| 10.4 Decision class dispatch (separate sub-scores per class) | Stage 10.1 | 1 day |
| 10.5 Historical calibration from replay data | Stage 10.3, Historical Replay | 1 day |
| 10.6 Logging and inspectability interface | Stage 10.2 | 1 day |
| 10.7 100+ tests (unit + integration) | Stage 10.1–10.6 | 3 days |

**Validation Gate**: Confidence engine produces consistent, inspectable confidence vectors for all decision classes. Sub-dimension scores are independently verifiable. Calibration metrics match manual calculation for known test cases. All 100+ tests pass.

**Critical Question**: What is the default confidence vector when no historical calibration exists? **Answer**: Zero across all dimensions, with maximum uncertainty. The system must not be confident without calibration data.

**GO / NO GO Checkpoint**: Pass → Stage 11. Fail → Return to Stage 10 and resolve.

---

### Stage 11 — Approval Engine Implementation

**Objective**: Implement the Approval Engine that consumes confidence vectors and produces decisions.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 11.1 Implement decision rule engine (threshold-based, policy-driven) | Stage 10 | 2 days |
| 11.2 Implement escalation logic (L0–L4) | Stage 11.1 | 2 days |
| 11.3 Implement risk veto and emergency stop connectors | Stage 11.1 | 1 day |
| 11.4 Implement human override interface (receive and log) | Stage 11.1 | 1 day |
| 11.5 Implement resource depletion check (connects to Stage 12) | Stage 12 (partial) | 1 day |
| 11.6 Decision audit log (append-only, structured) | Stage 11.1 | 1 day |
| 11.7 Integrate with lab CLI for manual approval testing | Stage 11.1–11.6, Lab CLI | 1 day |
| 11.8 80+ tests (unit + integration) | Stage 11.1–11.7 | 3 days |

**Validation Gate**: Approval Engine correctly emits all 4 decision types based on synthetic confidence vectors. Escalation chain works from L0 to L4. Risk veto independently blocks high-risk decisions. Emergency stop blocks all non-exit decisions. Human override is logged and time-bounded. All 80+ tests pass.

**GO / NO GO Checkpoint**: Pass → Stage 12. Fail → Return to Stage 11 and resolve.

---

### Stage 12 — Scarce Resources Measurement Layer

**Objective**: Implement runtime measurement of all 15 scarce resources.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 12.1 Capital measurement (free, deployed, drawdown) | Operational data access | 1 day |
| 12.2 Time measurement (cycle duration, deliberation time) | Stage 9 | 1 day |
| 12.3 Attention measurement (concurrent hypotheses, utilization) | Stage 9 | 1 day |
| 12.4 Energy/compute measurement (CPU, memory, API calls) | Infrastructure | 1 day |
| 12.5 Trust measurement (override rate, policy compliance) | Stage 11 | 1 day |
| 12.6 Knowledge measurement (count, confidence, decay state) | Stage 9, Scientific Lab | 1 day |
| 12.7 Other resources (proxy measurements) | Stage 12.1–12.6 | 2 days |
| 12.8 Resource conversion estimation | All measurement functions | 2 days |
| 12.9 60+ tests | Stage 12.1–12.8 | 2 days |

**Validation Gate**: All 15 resources are measurable in real-time (or at cycle granularity). Resource depletion alerts trigger at policy-defined thresholds. Resource conversion estimates are within 20% of observed values (validated against replay data). All 60+ tests pass.

**GO / NO GO Checkpoint**: Pass → Stage 13. Fail → Return to Stage 12.

---

### Stage 13 — Policy Configuration Layer

**Objective**: Implement the Decision Policy as a machine-readable, modifiable configuration.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 13.1 Policy parameter schema and storage | Stage 8 (Scientific Store) | 1 day |
| 13.2 Policy validation (contradiction detection) | Stage 13.1 | 1 day |
| 13.3 Policy modification interface (lab CLI subcommands) | Stage 13.1, Lab CLI | 2 days |
| 13.4 Policy versioning and change audit trail | Stage 13.1 | 1 day |
| 13.5 Autonomy ladder state management | Stage 13.1 | 1 day |
| 13.6 Policy-backed confidence vector aggregation functions | Stage 13.1, Stage 10 | 1 day |
| 13.7 Policy-backed approval thresholds | Stage 13.1, Stage 11 | 1 day |
| 13.8 40+ tests | Stage 13.1–13.7 | 2 days |

**Validation Gate**: Policy parameters are readable, writable, and validated. Contradictory policies are detected and rejected at load time. Policy changes are versioned and auditable. Autonomy ladder transitions are locked behind validation gates. All 40+ tests pass.

**GO / NO GO Checkpoint**: Pass → Stage 14. Fail → Return to Stage 13.

---

### Stage 14 — End-to-End Integration (No Real Capital)

**Objective**: Wire all components together in a simulation environment.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 14.1 Lab pipeline → Confidence Engine → Approval Engine integration | Stage 10, 11 | 2 days |
| 14.2 Resource measurement feeds confidence engine | Stage 12 | 1 day |
| 14.3 Policy configuration drives thresholds | Stage 13 | 1 day |
| 14.4 Paper trading integration (decisions flow through approval) | Stage 14.1, Paper Trading | 2 days |
| 14.5 Historical replay with full confidence/approval evaluation | Stage 14.1, Historical Replay | 2 days |
| 14.6 Manual approval testing workflow | Stage 14.1 | 1 day |
| 14.7 Autonomy ladder testing (all 6 stages) | Stage 14.1–14.6 | 2 days |
| 14.8 100+ integration tests | Stage 14.1–14.7 | 3 days |

**Validation Gate**: Full end-to-end flow works: lab analysis → confidence estimation → decision → audit log. Paper trading cycles produce approval decisions. All autonomy stages behave correctly. Emergency stop works end-to-end. Human override works. All 100+ integration tests pass.

**Minimum Evidence Before Proceeding**: Minimum 300 paper trading cycles with approval decisions logged and consistent.

**GO / NO GO Checkpoint**: Pass → Stage 15. Fail → Return to integration gap and resolve.

---

### Stage 15 — Calibration and Tuning

**Objective**: Tune policy thresholds using historical replay and paper trading data.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 15.1 Run historical replay through full DI pipeline (minimum 500 trades) | Stage 14, Historical Replay | 2 days |
| 15.2 Compute calibration curves per decision class | Stage 15.1 | 1 day |
| 15.3 Adjust threshold policy parameters for optimal calibration | Stage 15.2 | 2 days |
| 15.4 Validate adjusted parameters on held-out replay data | Stage 15.3 | 1 day |
| 15.5 Sensitivity analysis (which dimensions matter most?) | Stage 15.1 | 2 days |
| 15.6 Edge case discovery and remediation | Stage 15.1–15.5 | 3 days |

**Validation Gate**: Calibration error < 0.15 for all decision classes with at least 30 replayed examples. No systematic overconfidence or underconfidence bias > 0.05. Sensitivity analysis documented.

**Minimum Evidence**: 500 replayed trades minimum. 1000+ preferred.

**GO / NO GO Checkpoint**: Pass → Stage 16. Fail → Return to tuning and resolve calibration issues.

---

### Stage 16 — Paper Trading Validation

**Objective**: Run the full Decision Intelligence Layer alongside paper trading for extended validation.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 16.1 Integrate DI layer with paper trading engine (no real capital) | Stage 14 | 2 days |
| 16.2 Run minimum 100 paper trading cycles with DI approval | Stage 16.1 | Running time (days) |
| 16.3 Compare DI-approved decisions vs. paper trading results | Stage 16.2 | 1 day |
| 16.4 Analyze false positives (approved but lost) and false negatives (rejected but would have won) | Stage 16.3 | 2 days |
| 16.5 Adjust thresholds based on paper trading calibration | Stage 16.4 | 2 days |
| 16.6 Autonomy progression test: run at each ladder stage | Stage 16.5 | 3 days |

**Validation Gate**: Decision Intelligence Layer approval accuracy > 60% (better than random) for entry decisions. False positive rate (approved loss) < 30%. False negative rate (rejected win) < 40%. Calibration holds on out-of-sample data. Autonomy ladder behaves correctly at all stages.

**Minimum Evidence**: 100+ paper trading cycles with DI approval logged. System must demonstrate it rejects more bad opportunities than it misses good ones.

**GO / NO GO Checkpoint**: Pass → Stage 17. Fail → Return to calibration (Stage 15).

---

### Stage 17 — Small Real Capital Introduction

**Objective**: Deploy the Decision Intelligence Layer with real capital at minimum position size.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 17.1 Human review of all DI decisions (human-in-the-loop, Stage 1 autonomy) | Stage 16 | 1 day (setup) |
| 17.2 Run minimum 10 real-capital trades with DI approval + human confirmation | Stage 17.1 | Running time |
| 17.3 Compare DI confidence vs. real outcomes for first 10 trades | Stage 17.2 | 1 day |
| 17.4 Escalate any >2σ unexpected outcomes to criterion review | Stage 17.3 | 1 day |
| 17.5 Graduated position size increase (10% → 25% → 50% → 100% of standard sizing) | Stage 17.1–17.4 | Per-trade progression |

**Validation Gate**: First 10 real trades show no catastrophic outcomes. Calibration error on real trades is within 2× the calibration error observed in paper trading. No emergency stop triggered. All human overrides are logged and explained.

**Minimum Evidence**: 10 completed real trades with full cycle (entry → exit) under DI approval.

**Critical Risk**: Real capital introduces psychological factors (human operator stress, increased scrutiny) that paper trading does not replicate. The system must account for this in its confidence estimation.

**GO / NO GO Checkpoint**: Pass → Stage 18. Fail → Return to Stage 16, revert to paper trading, diagnose calibration gap.

---

### Stage 18 — Extended Real Capital Validation

**Objective**: Validate the DI layer across diverse market conditions with real capital.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 18.1 Run minimum 50 real-capital trades with DI approval + human confirmation | Stage 17 | Running time |
| 18.2 Validate across at least 2 distinct market regimes (trending, ranging, volatile) | Stage 18.1 | Running time (regime-dependent) |
| 18.3 Validate across multiple decision classes (entry, exit, sizing, skip) | Stage 18.1 | Running time |
| 18.4 Measure and analyze all scarce resource impacts | Stage 18.1, Stage 12 | 2 days |
| 18.5 Refine calibration with real data | Stage 18.1–18.4 | 3 days |

**Validation Gate**: 50+ real trades completed. No catastrophic losses (>10% account drawdown from peak). Calibration error on real trades < 0.20. Resource consumption tracking works correctly. At least one edge case discovered and handled.

**GO / NO GO Checkpoint**: Pass → Stage 19. Fail → Return to Stage 16 and re-evaluate DI readiness.

---

### Stage 19 — Supervised Autonomy (Stage 2)

**Objective**: Enable automatic approval with human timeout override.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 19.1 Enable automatic approval for Tier 1 decisions (exit, skip, evidence) | Stage 18 | 1 day |
| 19.2 Configure escalation timeout (human must respond within N minutes) | Stage 19.1 | 1 day |
| 19.3 Run minimum 30 cycles with supervised autonomy | Stage 19.1, 19.2 | Running time |
| 19.4 Validate no automatic decision caused unexpected harm | Stage 19.3 | 1 day |

**Validation Gate**: 30 cycles of supervised autonomy without incident. Human override rate < 10% of automatic decisions. Average human response time to escalations is consistently within timeout.

**GO / NO GO Checkpoint**: Pass → Stage 20. Fail → Return to Stage 18.

---

### Stage 20 — Conditional Autonomy (Stage 3)

**Objective**: Enable automatic approval for entry and sizing with elevated thresholds.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 20.1 Enable automatic entry approval with τ+30% elevated thresholds | Stage 19 | 1 day |
| 20.2 Enable automatic sizing approval with τ+20% elevated thresholds | Stage 20.1 | 1 day |
| 20.3 Run minimum 50 cycles with conditional autonomy | Stage 20.1, 20.2 | Running time |
| 20.4 Compare conditional autonomy performance vs. Stage 2 (supervised) | Stage 20.3 | 2 days |

**Validation Gate**: Conditional autonomy shows equivalent or better resource generation vs. supervised mode. No unexplained degradation. Human override rate < 5%.

**GO / NO GO Checkpoint**: Pass → Stage 21. Fail → Return to Stage 19 and analyze degradation.

---

### Stage 21 — High Autonomy (Stage 4)

**Objective**: Enable automatic approval for all decision classes except criterion changes.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 21.1 Enable standard threshold approval for all decision classes | Stage 20 | 1 day |
| 21.2 Enable automatic criterion delta application with human veto | Stage 21.1 | 1 day |
| 21.3 Run minimum 100 cycles with high autonomy | Stage 21.1, 21.2 | Running time |
| 21.4 Comprehensive autonomy audit | Stage 21.3 | 3 days |

**Validation Gate**: 100 cycles of high autonomy without incident. Resource generation per cycle is stable or improving. No escalation to emergency stop. Criterion maturity continues to increase (deltas proposed and applied at reasonable rate).

**GO / NO GO Checkpoint**: Pass → Stage 22. Fail → Return to Stage 20 and restrict autonomy.

---

### Stage 22 — Full Autonomy (Stage 5)

**Objective**: Enable full autonomous approval for all decision classes including criterion changes.

| Task | Dependencies | Effort Estimate |
|---|---|---|
| 22.1 Enable automatic criterion delta application without human veto | Stage 21 | 1 day |
| 22.2 Reduce escalation level to L1 for all routine decisions | Stage 22.1 | 1 day |
| 22.3 Run minimum 200 cycles with full autonomy | Stage 22.1, 22.2 | Running time |
| 22.4 Final autonomy validation | Stage 22.3 | 3 days |

**Validation Gate**: 200 cycles of full autonomy. Criterion maturity increases monotonically (or stable at high level). Calibration error consistently < 0.15. Scarce resources grow across multiple dimensions. Emergency stop never triggered (if triggered, autonomy is reduced one stage pending investigation).

**GO / NO GO Checkpoint**: Pass → Full autonomous approval capability achieved.

---

## 4. Dependency Graph

```
Stage 8 (Complete)
    ↓
Stage 9 ──────────────────────────────────────────────────────────────────┐
    ↓                                                                      │
Stage 10 ─────────────────────────────────────────────────────────────┐   │
    ↓                                                                  │   │
Stage 11 ───────────────────────────────────────────────┐             │   │
    ↓                                                    │             │   │
Stage 12 ───────────────────────────────┐               │             │   │
    ↓                                    │               │             │   │
Stage 13 ───────────────┐               │               │             │   │
    ↓                    │               │               │             │   │
Stage 14 ◄───────────────┴───────────────┴───────────────┴─────────────┴───┘
    ↓
Stage 15 (Calibration)
    ↓
Stage 16 (Paper Trading)
    ↓
Stage 17 (Small Real Capital)
    ↓
Stage 18 (Extended Real Capital)
    ↓
Stage 19 (Supervised Autonomy)
    ↓
Stage 20 (Conditional Autonomy)
    ↓
Stage 21 (High Autonomy)
    ↓
Stage 22 (Full Autonomy)
```

---

## 5. Cumulative Effort Estimate

| Stage | Days (Design + Implementation) | Days (Validation / Running) | Cumulative Days |
|---|---|---|---|
| 9 | 9 | 2 | 11 |
| 10 | 13 | 3 | 27 |
| 11 | 12 | 3 | 42 |
| 12 | 11 | 2 | 55 |
| 13 | 10 | 2 | 67 |
| 14 | 14 | Running | 81+ |
| 15 | 11 | 2 | 94 |
| 16 | 10 | Running (~100 cycles) | 104+ |
| 17 | 3 | Running (~10 trades) | 107+ |
| 18 | 5 | Running (~50 trades) | 112+ |
| 19 | 2 | Running (~30 cycles) | 114+ |
| 20 | 3 | Running (~50 cycles) | 117+ |
| 21 | 4 | Running (~100 cycles) | 121+ |
| 22 | 4 | Running (~200 cycles) | 125+ |

**Estimated calendar time to Stage 22**: 4–8 months, dominated by runtime validation (Stages 16–22 require hundreds of decision cycles).

---

## 6. Key Milestones

| Milestone | Stage | Criteria |
|---|---|---|
| **First real confidence estimate** | 10 | A confidence vector is computed for a real (historical) decision |
| **First approved decision** | 11 | The Approval Engine emits EXECUTE for a synthetic test case |
| **End-to-end integration** | 14 | Confidence → Approval → Audit works as a complete pipeline |
| **Calibration validated** | 15 | Brier score < 0.15 on held-out replay data |
| **Paper trading validated** | 16 | DI layer improves paper trading outcomes |
| **Real capital — first trade** | 17 | First real trade with DI approval |
| **Real capital — statistically meaningful** | 18 | 50+ real trades with consistent calibration |
| **First automatic decision** | 19 | System approves a non-critical decision without human |
| **First automatic entry** | 20 | System approves an entry decision with elevated thresholds |
| **First automatic criterion change** | 21 | System proposes and applies a criterion delta autonomously |
| **Full autonomy** | 22 | System operates without mandatory human review |

---

## 7. GO / NO GO Checkpoints (Consolidated)

| Checkpoint | Located At | Fail Action |
|---|---|---|
| Operational data readable (dry-run only) | Stage 9 | Resolve schema mismatch |
| Confidence engine passes 100+ tests | Stage 10 | Fix engine logic |
| Approval engine passes 80+ tests | Stage 11 | Fix engine logic |
| Resource measurement within 20% accuracy | Stage 12 | Fix measurement |
| Policy valid, no contradictions | Stage 13 | Fix policy parameters |
| End-to-end pipeline works in simulation | Stage 14 | Fix integration |
| Calibration error < 0.15 | Stage 15 | Return to tuning |
| DI improves paper trading (accuracy > 60%) | Stage 16 | Return to calibration |
| First 10 real trades without catastrophe | Stage 17 | Return to paper trading |
| 50+ real trades, calibration < 0.20 | Stage 18 | Return to calibration |
| Supervised autonomy: < 10% override rate | Stage 19 | Return to tuning |
| Conditional autonomy: no degradation vs supervised | Stage 20 | Return to supervised |
| High autonomy: 100 cycles, no incidents | Stage 21 | Restrict autonomy level |
| Full autonomy: 200 cycles, criterion increasing | Stage 22 | Reduce autonomy level |

---

## 8. Risks to the Roadmap

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Market regime change during validation invalidates calibration | Medium | High | Maintain separate calibration per regime; re-calibrate on regime detection |
| Human operator becomes bottleneck during Stage 17–18 | Medium | Medium | Design efficient review interfaces; batch approvals where possible |
| Real capital losses erode trust before Stage 18 completes | Low | Critical | Minimum position sizing; emergency stop always available; transparent loss reporting |
| Dependencies between DI components require rework of earlier stages | Medium | Medium | Clear interface contracts defined before implementation; integration tests at every stage |
| One-person maintainability boundary reached (engine too complex) | Low | High | Enforce 3000-line limit; refactor before adding features |
| Paper trading does not predict real trading performance | Medium | Critical | Assume gap exists; build in calibration correction factor; start with minimum capital |
| External dependencies (exchanges, data providers) change APIs | Medium | Medium | Isolate external access behind adapters; maintain local test fixtures |

---

## 9. Recommended Next Implementation Priority

**Immediate**: Stage 9 — Read-Only Operational Integration.

Rationale: All earlier stages depend on Stage 9 because the Confidence Engine needs real data for calibration, and the Approval Engine needs real decision contexts for testing. The lab currently runs on synthetic fixtures only. Connecting to real (but read-only) operational data is the critical path to every subsequent stage.

Stage 9 is also the lowest-risk stage — it involves no confidence estimation, no approval logic, no resource measurement. It is purely a data access layer with read-only guarantees, which is consistent with the current isolation between the scientific layer and operational components.

---

## 10. Open Design Questions

1. Should the roadmap include a "human trust recovery" stage between 18 and 19, where the system must demonstrate consistent performance before being granted any autonomy? **Current position**: Yes — Stage 18 validation already requires 50+ trades with consistent calibration. If additional trust-building is needed, a Stage 18.5 could be inserted.

2. How long should each autonomy stage be validated before progressing? **Current position**: Minimum cycle counts are specified per stage. If the system meets the validation gate criteria earlier than the minimum cycle count, it may progress. If it fails after the minimum, it regresses.

3. Should there be a "demotion" mechanism if the system's performance degrades after achieving a higher autonomy stage? **Current position**: Yes — autonomy is not a one-way ratchet. If calibration error exceeds threshold for a sustained period (>10 cycles), the autonomy stage is reduced automatically until the degradation is understood and resolved.

4. Is Stage 22 (full autonomy) a realistic target, or should the system always require human oversight for criterion changes? **Current position**: Full autonomy is the design target, but the policy can be configured to require human review for criterion changes indefinitely. Architecture supports both options.
