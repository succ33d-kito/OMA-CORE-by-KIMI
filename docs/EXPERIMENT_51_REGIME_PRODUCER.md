# Experiment 51 — prospective Regime producer (fail-closed activation)

Status: **IMPLEMENTED, QUALIFIED AND ACTIVATED BEFORE READINESS**
Date: 2026-10-16
Branch: `manual/51-real-policy-value-rule-20261016`
Baseline: `53e204f9ffd238a50ff3145b43e82b2634fde4fd`
Prereg (unchanged): `7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8`

Activating the producer is **not** activating a snapshot. Before an exactly-81-slot
role-authenticated contiguous window exists, the producer writes nothing, emits no
UNKNOWN/neutral/placeholder row, and reports `PRICE_HISTORY_NOT_READY` (or a more
specific reason) with exit code 0 (expected state, not an operational failure).

## 1. Input contract

Only role-authenticated `Price/OHLCV` evidence from the correct PILOT authority is
consumed. One attempt requires: 81 unique H1 slots, strict H1 contiguity, the exact
terminal slot, all 81 role attestations valid, causal availability of every input at
the cutoff, no conflicting observation for any slot, no missing slot, no future slot.

## 2. Candidate slot semantics

* primary candidate: `floor(now, H1)` — the most recent closed H1 boundary
  (`event_time` is the kline close; capture lands a few minutes later);
* bounded grace of exactly **one** slot: `floor(now, H1) - 1H`, used only if the
  primary is not yet evidenced, so a delayed invocation cannot silently skip an
  opportunity. Nothing older is ever eligible, so **no historical window can be
  backfilled** and there is no scan/catch-up/replay mode;
* the window is exactly `[S-80H .. S]`, certified by the frozen
  `price-81h-role-certificate-v1` convention. No alternative window convention.

## 3. Deterministic cutoff and idempotence

The window certificate is taken at `terminal + 5 min` — the frozen Experiment 51
`S+5m` raw cutoff — not at the wall-clock instant of the run. The same terminal
therefore always produces the same certificate id and source, so repeated runs are
idempotent (`ALREADY_ADMITTED`) instead of duplicating snapshots. Availability keeps
the qualified rule `available_at = max(computed_at, max(dependency.available_at))`
with `event_time <= received_at <= computed_at <= available_at`.

## 4. Fail-closed reasons

`PRICE_HISTORY_NOT_READY`, `PRICE_GAP`, `PRICE_ROLE_NOT_AUTHENTICATED`,
`AUTHORITY_MISMATCH`, `ROLE_MISMATCH`, `RAW_INPUT_NOT_CAUSAL`, `WINDOW_CONFLICT`,
`DERIVATION_RULE_MISMATCH`, `NOT_YET_CAUSAL`, and `ALREADY_ADMITTED` (idempotent,
never duplication).

## 5. Defect found and corrected in this cut

`derived_snapshot_admission.BUNDLE_FEATURES` was built directly from
`EXPECTED_FEATURES`, which is a **frozenset** whose iteration order depends on
`PYTHONHASHSEED`. The derived-snapshot schema hash and the Taker rule hash therefore
were **not reproducible across processes**. Corrected with a canonical sorted order
plus a `SCHEMA_HASH_NOT_REPRODUCIBLE` guard in `verify()` and a regression test.

Deterministic values (stable under seeds 1 / 7 / 12345):

```
REGIME_DERIVATION_RULE_HASH            = a3abeb1ad28f92af921464562fb37da587c0f4b01fd994b6ae81eb8bcab8d368
MECHANICS_TAKER_DERIVATION_RULE_HASH   = e33dee668bc1d5723033a5e44c7a8dcc7cf9af8bc8bb15c4e7a99eb953392dcd
DERIVED_SNAPSHOT_SCHEMA_HASH           = f3b218c7da8510929a88ab56da041592282503b6aa8fcba624c4c2b47fef8faa
DERIVED_ADMISSION_RULE_HASH            = cea20f9ed9a60070f53cabe63eda25f007d32a011cd64cc461bc8a85c2319bcc
BUNDLE_COMMITMENT                      = 93a8f22e8890e4c7b99dfac3086e05ff6b3b1192541d43e42b33a9713887ac5e
```

`DERIVED_ADMISSION_RULE_HASH` and `REGIME_DERIVATION_RULE_HASH` are unchanged from
the previous cut; only the two bundle-order-dependent hashes were corrected.

## 6. Qualification

`tests/test_regime_derived_operator.py` — **20 passed** — proves: 0 evidence writes
nothing; 80 slots write nothing; 81 contiguous produce exactly one snapshot; a gap
inside the window writes nothing; a bad role writes nothing; a wrong authority writes
nothing; future evidence is rejected; conflicting Price evidence is rejected; an
identical rerun is idempotent; no earlier historical eligible slot is backfilled; only
the current prospective candidate may be admitted; the snapshot binds the exact 81
source slots; the rule hash matches the frozen rule (and drift fails closed);
availability is causal; UNKNOWN is not emitted for missing data; no placeholder or
neutral state is written; restart preserves idempotence; producer state loss cannot
fabricate history; Experiment 51 can resolve the snapshot by exact id; P0 remains
independent of Regime.

Related suites: causal regime/mechanics/window + Experiment 51 derived/sealed +
policy value commitment = **121 passed**. `git diff --check` clean.

## 7. Activation and natural validation (2026-10-16)

* Runtime: `<REGIME_RUNTIME>` (MEDIUM, stdlib only),
  working directory `OMA-CORE-RUNTIME-REGIME51` (dedicated worktree at `15bd790`).
  Runtime qualification: compile OK on operator/CLI/binding, import OK, read-only SQLite access to
  the live role ledger OK (WAL lock respected), stdout JSON OK, `status` exit code 0, stderr empty.
  No live scientific derivation was performed during qualification.
* Task: `OMA-CORE-Experiment51-Regime-Derived`, `PT1H`, first boundary 2026-10-16T02:12+01:00,
  `MultipleInstances=IgnoreNew`, `ExecutionTimeLimit=PT5M`, principal `<LOCAL_OPERATOR>/Interactive/Limited`,
  action = existing `capture-process.ps1` + `regime/wrapper-config.json`.
  Rationale: the Price role captures the closed H1 kline a few minutes after the boundary
  (Mechanics pipeline observations land at slot+04:08); the producer certifies at the deterministic
  `terminal+5m` cutoff, so a `:12` invocation leaves ~7 minutes of margin over that cutoff, never
  races Price capture, never modifies the Price task, and keeps the snapshot available well before
  the `D = terminal+1h` decision.
* Activation gate: streak was **2** (< 81) and no eligible window existed, so activation could not
  create a snapshot.
* First natural invocation `20261016T0112020891209Z-8891f7c0d5f146c8ac431bd25ab1384f` at
  2026-10-16T01:12:02Z: exit code **0**, stderr **0 bytes**,
  `STATUS=NOT_READY REASON=PRICE_HISTORY_NOT_READY REGIME_SNAPSHOT_CREATED=false`.
  Ledger afterwards: `Regime/Role/v2` rows **0**; Price rows 57 → 58 and attestations 57 → 58 purely
  from the role's own natural capture of the 01:00Z slot. No backfill, no historical write.

Artifacts: `<OPS_DIAGNOSTICS>/51-scheduled-processes/regime/{wrapper-config.json,
task-definition.xml,activation-receipt.json}` plus the wrapper's stdout/stderr/meta diagnostics.

## 8. Explicit non-actions

No outcome/label inspection, no Experiment 51 execution, no DISCOVERY/CONFIRMATION
activation, no Kraken access, no Metrics/Mechanics/SEC modification, no EventDirection,
no event-population binding, no P0, no Price gap repair, no backfill, no Price
authority change, no prereg change, no `main` merge.
