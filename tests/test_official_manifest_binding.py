"""Synthetic official binding tests; no market or outcome data."""
from dataclasses import replace, FrozenInstanceError
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import pytest

from core.scientific import official_manifest_binding as b
from core.scientific.experimental_manifest import PopulationManifestBuilder, ExperimentalPopulationManifest
from core.scientific.nuisance_pilot_contracts import DatasetRole

_spec = importlib.util.spec_from_file_location("_binding_fixtures", Path(__file__).with_name("test_experimental_manifest.py"))
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
scope, manifest, T = _fixtures.scope, _fixtures.manifest, _fixtures.T


def test_persisted_freeze_retry_and_reopen(tmp_path):
    store, frozen = b.OfficialManifestStore(tmp_path), manifest()
    first = store.bind(scope(), frozen, T)
    path = tmp_path / (first.scope_id + ".json")
    original = path.read_bytes()
    assert store.bind(scope(), frozen, T) == first
    assert b.OfficialManifestStore(tmp_path).bind(scope(), frozen, T + timedelta(seconds=1)) == first
    assert path.read_bytes() == original
    assert json.loads(original)["manifest_id"] == frozen.manifest_id
    assert replace(first, bound_at=T + timedelta(seconds=1)).binding_id == first.binding_id
    assert replace(first, bound_at=T + timedelta(seconds=1)).artifact_id != first.artifact_id
    with pytest.raises(FrozenInstanceError):
        first.manifest_id = "0" * 64
    with pytest.raises(FrozenInstanceError):
        first.scope.run_id = "changed"


def test_building_rejected_without_mutation(tmp_path):
    builder = PopulationManifestBuilder(scope())
    with pytest.raises(TypeError, match="FROZEN"):
        b.OfficialManifestStore(tmp_path).bind(scope(), builder, T)
    assert list(tmp_path.iterdir()) == []
    assert builder.state.value == "BUILDING"


@pytest.mark.parametrize("change", [
    {"dataset_role": DatasetRole.CONFIRMATION}, {"run_id": "other"},
    {"protocol_hash": "other"}, {"population_rule_hash": "other"},
    {"population_cutoff": T + timedelta(seconds=1)},
])
def test_explicit_scope_mismatch(tmp_path, change):
    with pytest.raises(ValueError, match="scope/role mismatch"):
        b.OfficialManifestStore(tmp_path).bind(replace(scope(), **change), manifest(), T)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("change", [
    {"protocol_hash": "other"}, {"population_rule_hash": "other"},
    {"population_cutoff": T + timedelta(seconds=1)},
])
def test_cutoff_and_versions_cannot_evade_same_logical_scope(tmp_path, change):
    store = b.OfficialManifestStore(tmp_path)
    first = store.bind(scope(), manifest(), T)
    changed_scope = replace(scope(), **change)
    later = PopulationManifestBuilder(changed_scope).freeze(T + timedelta(seconds=2))
    with pytest.raises(ValueError, match="CONFLICT"):
        store.bind(changed_scope, later, T + timedelta(seconds=3))
    assert json.loads(next(tmp_path.iterdir()).read_text())["binding_id"] == first.binding_id


def test_later_population_cannot_replace_original(tmp_path):
    store = b.OfficialManifestStore(tmp_path)
    first = store.bind(scope(), manifest(), T)
    later = replace(manifest((_fixtures.opportunity(),)), frozen_at=T + timedelta(seconds=1))
    with pytest.raises(ValueError, match="CONFLICT"):
        store.bind(scope(), later, T + timedelta(seconds=2))
    assert len(list(tmp_path.iterdir())) == 1
    assert store.bind(scope(), manifest(), T) == first


def test_concurrent_competing_creates_have_one_winner(tmp_path):
    candidates = (manifest(), manifest((_fixtures.opportunity(),)))
    def attempt(candidate):
        try:
            return b.OfficialManifestStore(tmp_path).bind(scope(), candidate, T)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(attempt, candidates))
    winners = tuple(result for result in results if result is not None)
    assert len(winners) == 1
    paths = tuple(tmp_path.iterdir())
    assert len(paths) == 1
    assert paths[0].read_text() == winners[0].to_json() + "\n"


def test_same_manifest_id_different_artifact_rejected(tmp_path):
    frozen = manifest()
    altered = replace(frozen, frozen_at=T + timedelta(seconds=1))
    assert frozen.manifest_id == altered.manifest_id
    assert frozen.to_json() != altered.to_json()
    store = b.OfficialManifestStore(tmp_path)
    store.bind(scope(), frozen, T)
    with pytest.raises(ValueError, match="CONFLICT"):
        store.bind(scope(), altered, T + timedelta(seconds=2))


def test_subclass_cannot_spoof_identity(tmp_path):
    class Spoof(ExperimentalPopulationManifest):
        @property
        def manifest_id(self):
            return "0" * 64
    source = manifest()
    with pytest.raises(TypeError, match="exact FROZEN"):
        b.OfficialManifestStore(tmp_path).bind(scope(), Spoof(source.scope, source.records, T), T)


@pytest.mark.parametrize("content", ["", "{}", '{"bound_at":"2020-01-01T00:00:00+00:00","pnl":1}', "not json"])
def test_existing_invalid_artifact_never_overwritten(tmp_path, content):
    store = b.OfficialManifestStore(tmp_path)
    first = store.bind(scope(), manifest(), T)
    path = next(tmp_path.iterdir())
    path.write_text(content, encoding="utf-8")  # adversarial external tampering
    with pytest.raises(ValueError, match="CONFLICT"):
        store.bind(scope(), manifest(), T)
    assert path.read_text() == content


def test_time_constraints(tmp_path):
    store = b.OfficialManifestStore(tmp_path)
    for invalid in (T.replace(tzinfo=None), T - timedelta(seconds=1)):
        with pytest.raises(ValueError):
            store.bind(scope(), manifest(), invalid)
    assert list(tmp_path.iterdir()) == []
    first = store.bind(scope(), manifest(), T + timedelta(seconds=2))
    with pytest.raises(ValueError, match="CONFLICT"):
        store.bind(scope(), manifest(), T + timedelta(seconds=1))
    assert store.bind(scope(), manifest(), first.bound_at) == first


@pytest.mark.parametrize("name", ["outcome", "pnl", "performance", "ranking", "future_labels", "metadata"])
def test_outcome_inputs_rejected(tmp_path, name):
    with pytest.raises(TypeError):
        b.OfficialManifestStore(tmp_path).bind(scope(), manifest(), T, **{name: "forbidden"})
    assert list(tmp_path.iterdir()) == []


def test_process_order_independent_and_compile(tmp_path):
    script = ("import sys;sys.path.insert(0,'tests');import test_official_manifest_binding as t;"
              "ops=(t._fixtures.opportunity(),t._fixtures.other_op());"
              "ops=ops[::-1] if sys.argv[2]=='reverse' else ops;"
              "print(t.b.OfficialManifestStore(sys.argv[1]).bind(t.scope(),t.manifest(ops),t.T).binding_id)")
    results = [subprocess.check_output([sys.executable, "-B", "-c", script, str(tmp_path / seed), order],
        text=True, cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"})
        for order, seed in (("forward", "13"), ("reverse", "79"))]
    assert results[0] == results[1]
    compile(Path(b.__file__).read_text(encoding="utf-8"), b.__file__, "exec")
