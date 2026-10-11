from datetime import timedelta
import json
import sqlite3

import pytest

from core.scientific import metrics_observation_admission as admission
from core.scientific.prospective_receipts import (
    append_observation,
    load_observations,
)
from tests.test_metrics_continuity import (
    S,
    capture,
    state,
)


def admit(state, ledger, *, now=None, clock=None):
    return admission.admit_verified_metrics_bundle(
        ledger,
        state[0],
        S,
        repo_root=state[1],
        now=now or S + timedelta(minutes=5),
        clock=clock or (
            lambda: S + timedelta(minutes=5)
        ),
    )


def test_atomic_success_admits_exactly_six_shared_bundle_rows(
    state,
    tmp_path,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    result = admit(state, ledger)

    assert result["status"] == "ADMITTED"
    assert result["row_count"] == 6

    rows = load_observations(ledger)

    assert len(rows) == 6
    assert {
        row["feature"]
        for row in rows.values()
    } == admission.EXPECTED_FEATURES

    assert {
        row["available_at"]
        for row in rows.values()
    } == {
        (S + timedelta(minutes=5)).isoformat()
    }

    assert {
        row["provenance"]["bundle_id"]
        for row in rows.values()
    } == {
        result["bundle_id"]
    }

    assert all(
        row["derived"] is False
        and row["dependencies"] == []
        and row["computed_at"] is None
        for row in rows.values()
    )


def test_identical_readmission_is_idempotent(
    state,
    tmp_path,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    first = admit(state, ledger)

    with sqlite3.connect(ledger) as con:
        before = con.execute(
            """
            SELECT seq,id,body,previous_hash,receipt_hash
            FROM observations_v2
            ORDER BY seq
            """
        ).fetchall()

    second = admit(
        state,
        ledger,
        clock=lambda: S + timedelta(minutes=6),
        now=S + timedelta(minutes=6),
    )

    with sqlite3.connect(ledger) as con:
        after = con.execute(
            """
            SELECT seq,id,body,previous_hash,receipt_hash
            FROM observations_v2
            ORDER BY seq
            """
        ).fetchall()

    assert first["status"] == "ADMITTED"
    assert second["status"] == "ALREADY_ADMITTED"
    assert first["bundle_id"] == second["bundle_id"]
    assert before == after
    assert len(after) == 6


def test_sql_failure_rolls_back_all_six_rows(
    state,
    tmp_path,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    # Initialize schema, then create a deliberate mid-transaction failure.
    assert load_observations(ledger) == {}

    with sqlite3.connect(ledger) as con:
        con.execute(
            """
            CREATE TRIGGER forced_metrics_atomicity_failure
            BEFORE INSERT ON observations_v2
            WHEN instr(
                NEW.body,
                'MarketMetrics/TakerBuySellRatio'
            ) > 0
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'forced atomicity fault'
                );
            END
            """
        )

    with pytest.raises(
        sqlite3.DatabaseError,
        match="forced atomicity fault",
    ):
        admit(state, ledger)

    with sqlite3.connect(ledger) as con:
        count = con.execute(
            "SELECT COUNT(*) FROM observations_v2"
        ).fetchone()[0]

    assert count == 0


def test_corrupt_capture_never_reaches_ledger(
    state,
    tmp_path,
):
    capture(state)

    raw = (
        state[0]
        / "attempts"
        / "20261011T130000Z"
        / "capture"
        / "raw"
        / "oi.json"
    )
    raw.write_bytes(b"[]")

    ledger = tmp_path / "scientific.db"

    with pytest.raises(ValueError):
        admit(state, ledger)

    assert load_observations(ledger) == {}


def test_future_unavailable_capture_is_rejected(
    state,
    tmp_path,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    with pytest.raises(ValueError):
        admit(
            state,
            ledger,
            now=S,
            clock=lambda: S,
        )

    assert load_observations(ledger) == {}


def test_late_historical_admission_is_rejected(
    state,
    tmp_path,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    late = S + timedelta(days=2)

    with pytest.raises(
        ValueError,
        match="historical backfill",
    ):
        admit(
            state,
            ledger,
            now=late,
            clock=lambda: late,
        )

    assert load_observations(ledger) == {}


def test_existing_semantic_conflict_fails_closed(
    state,
    tmp_path,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    append_observation(
        ledger,
        source="https://example.invalid/metric",
        instrument="BTCUSDT",
        feature="MarketMetrics/OpenInterest",
        event_time=S,
        source_metric_at=S - timedelta(microseconds=1),
        received_at=S + timedelta(minutes=1),
        payload={"value": 999.0},
        provenance={"contract": "test-conflict"},
        clock=lambda: S + timedelta(minutes=2),
    )

    with pytest.raises(
        ValueError,
        match="conflicting Metrics observation",
    ):
        admit(state, ledger)

    assert len(load_observations(ledger)) == 1
def test_evidence_mutation_between_projection_and_admission_rejected(
    state,
    tmp_path,
    monkeypatch,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    original = admission.load_verified_bundle
    calls = {"count": 0}

    def load_then_mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        calls["count"] += 1

        if calls["count"] == 1:
            raw = (
                state[0]
                / "attempts"
                / "20261011T130000Z"
                / "capture"
                / "raw"
                / "oi.json"
            )
            raw.write_bytes(b"[]")

        return result

    monkeypatch.setattr(
        admission,
        "load_verified_bundle",
        load_then_mutate,
    )

    with pytest.raises(ValueError):
        admit(state, ledger)

    assert load_observations(ledger) == {}


def test_ledger_corruption_after_preflight_is_rejected_inside_transaction(
    state,
    tmp_path,
    monkeypatch,
):
    capture(state)
    ledger = tmp_path / "scientific.db"

    append_observation(
        ledger,
        source="https://example.invalid/existing",
        instrument="BTCUSDT",
        feature="Test/Existing",
        event_time=S,
        source_metric_at=S,
        received_at=S + timedelta(minutes=1),
        payload={"value": 1.0},
        provenance={"contract": "test-existing"},
        clock=lambda: S + timedelta(minutes=2),
    )

    original = admission.observation_snapshot

    def verify_then_corrupt(path, *args, **kwargs):
        result = original(
            path,
            *args,
            **kwargs,
        )

        with sqlite3.connect(path) as con:
            con.execute(
                "DROP TRIGGER observations_v2_no_update"
            )
            con.execute(
                """
                UPDATE observations_v2
                SET receipt_hash=?
                WHERE seq=1
                """,
                ("0" * 64,),
            )

        return result

    monkeypatch.setattr(
        admission,
        "observation_snapshot",
        verify_then_corrupt,
    )

    with pytest.raises(
        ValueError,
        match="chain digest",
    ):
        admit(state, ledger)

    with sqlite3.connect(ledger) as con:
        count = con.execute(
            "SELECT COUNT(*) FROM observations_v2"
        ).fetchone()[0]

    assert count == 1
