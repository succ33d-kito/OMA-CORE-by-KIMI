# Experiment 51 — admitted derived snapshot binding (Regime + Taker Mechanics)

Status: **BINDING IMPLEMENTED AND QUALIFIED (engineering portion)**
Live derived snapshots: **Mechanics available (5, naturally produced); Regime NOT available**
Date: 2026-10-16
Branch: `manual/51-real-policy-value-rule-20261016` (continues the qualified lineage)
Baseline: `15b685729522a3090d05078a4049521ecd9b650b`
Canonical prereg (unchanged): `7121a21d711064ee8bdc94f7269e65f006674684f65cbd715ea2044a7ba51de8`

## 1. What already existed

The causal snapshot infrastructure was already in place and is reused, not duplicated:

* `prospective_receipts.append_observation` — append-only `observations_v2` hash chain; assigns
  `computed_at`/`available_at` itself, never from the caller; idempotent for an identical identity,
  **conflict-rejecting** ("conflicting observation; no silent overwrite"); rejects
  `received > now` / `event > received` / `event older than 24h` (no backfill, no backdating).
* `causal_regime` (`Regime/Role/v2`, contract `causal-role-regime-v2`) — derives from a certified
  **81 contiguous role-authenticated H1** price window, requires `computed_at >= cutoff`, validates by
  full reconstruction.
* `causal_mechanics` (`Mechanics/Descriptive/v1`, contract `causal-descriptive-mechanics-v1`) —
  builds from the admitted causal observation snapshot, requires a non-empty dependency set and
  `computed_at >= cutoff`, and validates the exact availability identity
  `available_at == max(computed_at, dependency.available_at)` with
  `event_time <= received_at <= computed_at <= available_at <= cutoff`.
* `role_price_window` — the `price-81h-role-certificate-v1` window certificate
  (exactly 81 unique, contiguous, role-attested, causally available, conflict-free).
* `experiment51_derived.derived` — already consumes **IDs**, never computes ad hoc: it validates
  `regime_id` / `mechanics_id` through the validators, requires the exact terminal slot `S = D-1H`,
  `available_at <= S+5m`, one atomic bundle, and extracts Taker only
  (`MarketMetrics/TakerBuySellRatio`); regime/funding contamination is rejected.

## 2. What this cut adds (additive)

`core/scientific/derived_snapshot_admission.py` — the prospective admission operator and the explicit
commitment binding:

* **Typed fail-closed outcomes**: `PRICE_HISTORY_NOT_READY`, `METRICS_HISTORY_NOT_READY`,
  `RAW_INPUT_NOT_ADMITTED`, `AUTHORITY_MISMATCH`, `ROLE_MISMATCH`, `PUBLICATION_NOT_CAUSAL`,
  `DERIVATION_NOT_AVAILABLE`, `BUNDLE_NOT_ATOMIC`. Missing data never becomes UNKNOWN, zero or a
  neutral value, and nothing is written when a prerequisite fails.
* **Taker-only, atomic-bundle enforcement** for Experiment 51: the six-value bundle must be present
  and regime/funding must be absent from the Taker information set.
* **Arm binding**: `P0 → ()`, `PR → (REGIME,)`, `PM → (MECHANICS_TAKER,)`,
  `PRM → (REGIME, MECHANICS_TAKER)`, matching the frozen `RULES`/`families()` semantics.
* `require_admitted_regime` / `require_admitted_taker_mechanics` return the exact persisted rows
  Experiment 51 may consume.

Committed identifiers:

```
REGIME_DERIVED_SCHEMA            = causal-role-regime-v2
MECHANICS_DERIVED_SCHEMA         = causal-descriptive-mechanics-v1
REGIME_DERIVATION_RULE_ID        = exp51-regime-role-v2
REGIME_DERIVATION_RULE_HASH      = a3abeb1ad28f92af921464562fb37da587c0f4b01fd994b6ae81eb8bcab8d368
MECHANICS_TAKER_DERIVATION_RULE_ID   = exp51-mechanics-taker-v1
MECHANICS_TAKER_DERIVATION_RULE_HASH = 33adaea7d3f4539ffed8c4f444c6b841ef886b87deab4f77acff21d2038a4e91
DERIVED_SNAPSHOT_SCHEMA_HASH     = e041b7ada8f75ca7cb8f29a033bad9cddbadbbeb4629eea08157d90de79683da
DERIVED_ADMISSION_RULE_HASH      = cea20f9ed9a60070f53cabe63eda25f007d32a011cd64cc461bc8a85c2319bcc
BUNDLE_COMMITMENT                = f839f63d391fcd61064be1256b6d4e7755f976456c0fc309c1a37be38e6ddcae
DERIVED_AVAILABILITY_RULE        = available_at = max(computed_at, max(dependency.available_at));
                                   event_time <= received_at <= computed_at <= available_at <= cutoff
```

## 3. Qualification (TEST evidence only)

`tests/test_derived_snapshot_admission.py` — **30 passed** — covers the 28 required properties plus the
commitment checks: <81 slots, in-window gap, unauthenticated role, exact window reference, availability
vs raw input / computation / durable publication, missing Metrics history, Taker-only input, partial
bundle rejection, unauthenticated Metrics role, exact bundle identities, causal availability identity,
missing ≠ UNKNOWN, missing ≠ zero, idempotent duplicate, conflicting duplicate, historical publication
rows unchanged, no backdating, future evidence rejected, PR/PM/PRM require the admitted snapshot, P0
independent, no ad-hoc derivation in evaluation, role/authority/rule-hash mismatches fail closed.

Related suites: `test_causal_regime` + `test_causal_mechanics` + `test_role_price_window` +
`test_causal_observation_snapshot` + `test_causal_dataset_role` = **25 passed**;
`test_experiment51_derived` + `test_experiment51_sealed` + `test_policy_value_commitment` =
**114 passed**; `git diff --check` clean.

Passing these tests does **not** mean live derived readiness. It means the binding and operator are
qualified.

## 4. Live state (read-only, 2026-10-16)

* **Mechanics: available.** The production operator `metrics_admission_operator.py` already calls
  `append_causal_mechanics(..., dataset_role='PILOT', cutoff=raw_cut)`; five admitted snapshots exist
  in `metrics-admission-v1/observations.sqlite` (slots 2026-10-15T00:00Z, 21:00Z, 22:00Z, 23:00Z and
  2026-10-16T00:00Z). Each has the atomic six-value bundle, Taker present, no funding, no regime,
  `computed_at == available_at == slot + 04:08`, all validating PASS. They satisfy the `S+5m` causal
  cutoff of the frozen decision rule.
* **Regime: not available.** No `Regime/Role/v2` snapshot exists in any ledger. The role ledger holds
  57 `Price/OHLCV` rows with 57 attestations (PILOT) and only 52 contiguous pairs; the current
  role streak is 2 — below the required 81 contiguous slots.
* Historical Metrics publications were re-read only: `mechanics_id` remains `null` in all 17 rows.
  Nothing was rewritten, backfilled or repaired.

## 5. Activation

Mechanics derivation is already active in production (no new authority needed). No production caller
of `append_causal_regime` exists, so emitting the first Regime snapshot requires an explicit,
separately authorized activation once 81 contiguous role-authenticated slots naturally exist. No
snapshot was fabricated in this cut.

## 6. Explicit non-actions

No outcome/label inspection, no Experiment 51 execution, no DISCOVERY/CONFIRMATION activation, no
Kraken access, no EventDirection creation, no P0, no event-population binding, no Price/Metrics/SEC
capture change, no gap repair, no backfill, no rewrite of existing Metrics publications, no prereg
modification, no `main` merge.
