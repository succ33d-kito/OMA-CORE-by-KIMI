# Regime producer cut: forensic closure, 2026-10-16

Resume baseline: c2b01fde4d6913f6dc137e7b0a31b4128eb75cff (clean).
Implementation: 15bd7906c86aaac42b44a1538be9702a8041a0cf.
Scientific parent: 53e204f9ffd238a50ff3145b43e82b2634fde4fd.
Branch: manual/51-real-policy-value-rule-20261016. No reset, main merge or runtime update.
The closing documentation commit c2b01fd already existed; activation was not repeated.

## Commitment genealogy

Historical source at 53e204f constructs BUNDLE_FEATURES from an unordered frozenset.
Schema and Taker rule consume that tuple directly. The bundle consumes both hashes
AND atomic_bundle_features. Regime and admission hashes do not consume it.
Six separate processes (PYTHONHASHSEED 0, 1, 7, 42, 12345, random) reproduced
six distinct old schema/Taker/bundle digests each, and one distinct value each
for every canonical commitment. Regime and admission were identical old/new.
Enumerating the 720 feature permutations reproduced all three previously reported
old digests exactly, with the SAME feature ordering. No scientific data was involved.

OLD_COMMITMENT_STATUS=RETIRED_NONDETERMINISTIC for exactly these three values:

```
OLD_DERIVED_SNAPSHOT_SCHEMA_HASH=e041b7ada8f75ca7cb8f29a033bad9cddbadbbeb4629eea08157d90de79683da
OLD_MECHANICS_DERIVATION_RULE_HASH=33adaea7d3f4539ffed8c4f444c6b841ef886b87deab4f77acff21d2038a4e91
OLD_BUNDLE_COMMITMENT=f839f63d391fcd61064be1256b6d4e7755f976456c0fc309c1a37be38e6ddcae
```

NEW_COMMITMENT_STATUS=CANONICAL:

```
REGIME_DERIVATION_RULE_HASH=a3abeb1ad28f92af921464562fb37da587c0f4b01fd994b6ae81eb8bcab8d368
NEW_MECHANICS_DERIVATION_RULE_HASH=e33dee668bc1d5723033a5e44c7a8dcc7cf9af8bc8bb15c4e7a99eb953392dcd
MECHANICS_TAKER_DERIVATION_RULE_HASH=e33dee668bc1d5723033a5e44c7a8dcc7cf9af8bc8bb15c4e7a99eb953392dcd
NEW_DERIVED_SNAPSHOT_SCHEMA_HASH=f3b218c7da8510929a88ab56da041592282503b6aa8fcba624c4c2b47fef8faa
DERIVED_SNAPSHOT_SCHEMA_HASH=f3b218c7da8510929a88ab56da041592282503b6aa8fcba624c4c2b47fef8faa
DERIVED_ADMISSION_RULE_HASH=cea20f9ed9a60070f53cabe63eda25f007d32a011cd64cc461bc8a85c2319bcc
BUNDLE_COMMITMENT=93a8f22e8890e4c7b99dfac3086e05ff6b3b1192541d43e42b33a9713887ac5e
AFFECTED_OLD_HASHES=DERIVED_SNAPSHOT_SCHEMA_HASH,MECHANICS_TAKER_DERIVATION_RULE_HASH,BUNDLE_COMMITMENT
UNAFFECTED_HASHES=REGIME_DERIVATION_RULE_HASH,DERIVED_ADMISSION_RULE_HASH
COMMITMENTS_CROSS_PROCESS_REPRODUCIBLE=YES
```

Unaffected scope is the five commitments traced here; this does not certify every
unrelated repository digest. The prior producer document's phrase "only the two"
omitted the transitive bundle impact. This record supersedes that interpretation.
Commit 15bd790 had replaced hashes and damaged UTF-8 in the historical binding
report. This closure restores that report's original 53e204f content and appends
a retirement notice; old commits and operational receipts remain untouched.
Reproducer: scripts/audit_regime_commitment_determinism.py; process output:
docs/EXPERIMENT_51_REGIME_HASH_PROCESS_EVIDENCE.json.

## Existing task and runtime (read-only inspection)

```
TASK_NAME=OMA-CORE-Experiment51-Regime-Derived
TASK_EXISTS=YES
TASK_ENABLED=YES
TASK_STATE=Ready
TASK_INTERVAL=PT1H
TASK_EXECUTE=<POWERSHELL_RUNTIME>
TASK_ARGUMENTS=-NoProfile -NonInteractive -File "<OPS_DIAGNOSTICS>\51-scheduled-processes\capture-process.ps1" -Config "<OPS_DIAGNOSTICS>\51-scheduled-processes\regime\wrapper-config.json"
TASK_WORKING_DIRECTORY=(not set in task XML; wrapper sets runtime worktree below)
TASK_MULTIPLE_INSTANCES_POLICY=IgnoreNew
TASK_DUPLICATE_PRESENT=NO
RUNTIME_PATH=<REGIME_RUNTIME>
RUNTIME_WORKING_DIRECTORY=<OMA_CORE_RUNTIME_REGIME51>
RUNTIME_ARGUMENTS=-B "<OMA_CORE_RUNTIME_REGIME51>\scripts\regime_snapshot.py" --root "<OMA_DATA_ROOT>\prospective\price-role-h1-v1" once
RUNTIME_HEAD=15bd7906c86aaac42b44a1538be9702a8041a0cf
RUNTIME_QUALIFIED=YES
RUNTIME_INTEGRITY=MEDIUM (existing qualification receipt; not independently retoken-tested)
```

Task inventory matched name and action references: exactly one. Last task result 0,
last boundary 2026-10-16T01:12Z, next 02:12Z, missed runs 0. Runtime worktree clean.
Existing import/compile/SQLite/lock/stdout/exit qualification is recorded in the
producer document and activation receipt; resume independently ran only read-only
status, which exited 0 with JSON. No once invocation occurred during resume.

## First natural evidence

```
FIRST_NATURAL_INVOCATION_ID=20261016T0112020891209Z-8891f7c0d5f146c8ac431bd25ab1384f
FIRST_NATURAL_STARTED_AT=2026-10-16T01:12:02.1086972Z
FIRST_NATURAL_COMPLETED_AT=2026-10-16T01:12:02.6694401Z
FIRST_NATURAL_EXIT_CODE=0
FIRST_NATURAL_STATUS=NOT_READY / PRICE_HISTORY_NOT_READY
REGIME_SNAPSHOT_COUNT_BEFORE=0
REGIME_SNAPSHOT_COUNT_AFTER_FIRST_NATURAL_RUN=0
REGIME_SNAPSHOT_CREATED=NO
```

The original start/completion metadata, stdout and activation receipt agree.
stdout SHA256=8cad12647b631fff5d0134bb67fd9602201f7cc2ed9ee4a68397d2b23630579e;
stderr empty. Current append-only ledger chain verifies; no Regime rows exist.
Before/after counts are supported by the contemporaneous receipt and current
verified chain, not by a newly fabricated historical ledger snapshot.

## Qualification and live readiness

Resume tests in <AUDIT_ENV>: 51 passed in 137.03s.
REGIME_PRODUCER_TESTS_PASS=YES (20)
DERIVED_BINDING_TESTS_PASS=YES (31)
HASH_DETERMINISM_TESTS_PASS=YES (six old/new subprocess pairs; exact old-value reproduction)
GIT_DIFF_CHECK=PASS
The initially selected oma-51-validation interpreter lacked pytest; no test failed
there. Tests were rerun successfully in the existing oma-audit environment.

Read-only runtime status observed 2026-10-16T01:27:18.933780Z:
LIVE_PRICE_CURRENT_STREAK=3
LIVE_PRICE_SLOTS_TO_81=78
LATEST_PRICE_ROLE_SLOT=2026-10-16T01:00:00+00:00
LIVE_REGIME_SNAPSHOT_AVAILABLE=NO
REGIME_PRODUCER_IMPLEMENTED=YES
REGIME_PRODUCER_QUALIFIED=YES
REGIME_PRODUCER_ACTIVATED=YES
ADMITTED_DERIVED_SNAPSHOTS_NOT_BOUND_STRUCTURALLY_RESOLVED=YES
MECHANICS_EXP51_INPUT_GATE=PASS (six existing PILOT snapshots validated by require_admitted_taker_mechanics)
REGIME_EXP51_INPUT_GATE=FAIL

Mechanics PASS is a live admitted-input availability finding, not certification
of every future decision slot or a DISCOVERY population. Six snapshots validated
from metrics-admission-v1/observations.sqlite, with chain verification.

HISTORICAL_REGIME_BACKFILL_PERFORMED=NO
PRICE_HISTORY_REWRITTEN=NO
SCIENTIFIC_HISTORY_REWRITTEN=NO
No scientific writes were performed by resume. Tests used isolated synthetic data.
No outcomes, Experiment 51 execution, phase activation, Kraken, SEC/Price/Metrics/
Mechanics production change, prereg mutation or main merge.

## Next cut: read-only readiness findings

The frozen prereg still lists OFFICIAL_EVENT_POPULATION_NOT_BOUND and
FUTURE_ROLE_ACTIVATIONS_AND_PHASE_STARTS_NOT_BOUND. Its minimum support remains
2160 calendar hours per phase, 200 paired opportunities, 200 active per arm and
12 blocks with opportunities. 81H readiness does not replace statistical support.
The existing READINESS document predates derived-binding qualification and still
describes unimplemented gates; its CLI must not be interpreted as current closure
authority without tracing later bindings.

Recommended next non-world-dependent cut: audit/design the official event-population
binding and its causal identity/CS4 interface against the frozen prereg, with no
population admission, outcome access or phase start. This remains a separate
authorized task. Natural eligible BTC events and 81H Price support remain world-
dependent; DISCOVERY/CONFIRMATION activation requires explicit authorization.
