from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import core.scientific.funding_continuity as fc


T = datetime(
    2026,
    10,
    10,
    0,
    0,
    0,
    tzinfo=timezone.utc,
)


def write_json(
    path,
    value,
):
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
        encoding="utf-8",
    )


def sid(slot):
    return fc.slot_id(slot)


def make_attempt(
    state,
    slot,
    *,
    status="SUCCESS",
    receipt_id=None,
):
    path = (
        Path(state)
        / "attempts"
        / sid(slot)
    )

    path.mkdir(
        parents=True,
        exist_ok=False,
    )

    started = (
        slot
        + timedelta(seconds=15)
    )

    write_json(
        path / "attempt.json",
        {
            "schema":
                fc.ATTEMPT_SCHEMA,
            "contract":
                fc.CONTRACT,
            "slot":
                slot.isoformat(),
            "target_at":
                fc.target_at(
                    slot
                ).isoformat(),
            "deadline_at":
                fc.deadline_at(
                    slot
                ).isoformat(),
            "started_at":
                started.isoformat(),
            "status":
                "STARTED",
        },
    )

    if status == "INCOMPLETE":
        return path

    if status == "SUCCESS":

        if receipt_id is None:
            receipt_id = (
                "receipt-"
                + sid(slot)
            )

        (
            path / "capture"
        ).mkdir()

        error = None

    elif status == "FAILED":

        receipt_id = None
        error = "transport failure"

    else:
        raise ValueError(
            status
        )

    write_json(
        path / "result.json",
        {
            "schema":
                fc.RESULT_SCHEMA,
            "contract":
                fc.CONTRACT,
            "slot":
                slot.isoformat(),
            "status":
                status,
            "completed_at":
                (
                    slot
                    + timedelta(
                        minutes=3
                    )
                ).isoformat(),
            "capture_receipt_id":
                receipt_id,
            "error":
                error,
        },
    )

    return path


def install_fake_loader(
    monkeypatch,
    *,
    request_offsets=None,
    receipt_overrides=None,
):
    request_offsets = (
        request_offsets
        or {}
    )

    receipt_overrides = (
        receipt_overrides
        or {}
    )

    def fake_load(
        capture_path,
    ):
        capture_path = Path(
            capture_path
        )

        slot_name = (
            capture_path
            .parent
            .name
        )

        slot = datetime.strptime(
            slot_name,
            "%Y%m%dT%H0000Z",
        ).replace(
            tzinfo=timezone.utc
        )

        offset = (
            request_offsets.get(
                slot_name,
                15,
            )
        )

        request_started = (
            slot
            + timedelta(
                seconds=offset
            )
        )

        received = (
            request_started
            + timedelta(seconds=1)
        )

        available = (
            received
            + timedelta(seconds=1)
        )

        receipt_id = (
            receipt_overrides.get(
                slot_name
            )
            or (
                "receipt-"
                + slot_name
            )
        )

        receipt = SimpleNamespace(
            receipt_id=receipt_id,
            request_started_at=
                request_started,
            received_at=received,
            available_at=available,
        )

        return SimpleNamespace(
            instrument="BTCUSDT",
            venue="Binance USDⓈ-M",
            product="linear perpetual",
            dataset_role=
                SimpleNamespace(
                    value="PILOT"
                ),
            decision_at=available,
            receipts=(receipt,),
        )

    monkeypatch.setattr(
        fc,
        "load_premium",
        fake_load,
    )


def reference_after(
    slot,
):
    return (
        slot
        + timedelta(minutes=2)
    )


def test_due_slot_not_due_before_deadline():
    before = (
        T
        + timedelta(
            seconds=119,
            microseconds=999999,
        )
    )

    assert fc.due_slots(
        T,
        before,
    ) == ()

    assert fc.due_slots(
        T,
        T + timedelta(minutes=2),
    ) == (T,)


def test_missing_due_slot_is_missed(
    tmp_path,
):
    report = fc.status(
        tmp_path,
        T,
        T + timedelta(minutes=2),
    )

    assert (
        report["total_expected_slots"]
        == 1
    )

    assert (
        report["missed_slots"]
        == 1
    )

    assert (
        report["current_streak"]
        == 0
    )

    assert (
        report["slots_to_81"]
        == 81
    )

    assert (
        report["funding_81h_ready"]
        is False
    )


def test_incomplete_attempt_breaks_streak(
    tmp_path,
):
    make_attempt(
        tmp_path,
        T,
        status="INCOMPLETE",
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report["incomplete_slots"]
        == 1
    )

    assert (
        report["current_streak"]
        == 0
    )


def test_failed_attempt_breaks_streak(
    tmp_path,
):
    make_attempt(
        tmp_path,
        T,
        status="FAILED",
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report["failed_slots"]
        == 1
    )

    assert (
        report["current_streak"]
        == 0
    )


def test_valid_success_counts(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    make_attempt(
        tmp_path,
        T,
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report["successful_slots"]
        == 1
    )

    assert (
        report["current_streak"]
        == 1
    )

    assert (
        report["longest_streak"]
        == 1
    )

    assert (
        report["slots_to_81"]
        == 80
    )


def test_80_successes_are_not_ready(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    for i in range(80):
        make_attempt(
            tmp_path,
            T + i * fc.HOUR,
        )

    last = (
        T
        + 79 * fc.HOUR
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(last),
    )

    assert (
        report["current_streak"]
        == 80
    )

    assert (
        report["slots_to_81"]
        == 1
    )

    assert (
        report["funding_81h_ready"]
        is False
    )

    assert (
        report["certificate"]
        is None
    )


def test_81_successes_create_certificate(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    for i in range(81):
        make_attempt(
            tmp_path,
            T + i * fc.HOUR,
        )

    last = (
        T
        + 80 * fc.HOUR
    )

    reference = (
        reference_after(last)
    )

    report = fc.status(
        tmp_path,
        T,
        reference,
    )

    assert (
        report["current_streak"]
        == 81
    )

    assert (
        report["slots_to_81"]
        == 0
    )

    assert (
        report["funding_81h_ready"]
        is True
    )

    cert = report[
        "certificate"
    ]

    assert (
        cert["schema"]
        == fc.CERTIFICATE_SCHEMA
    )

    assert (
        cert["number_of_slots"]
        == 81
    )

    assert (
        len(
            cert["slot_ids"]
        )
        == 81
    )

    assert (
        len(
            cert[
                "capture_receipt_ids"
            ]
        )
        == 81
    )

    assert (
        cert["first_slot"]
        == T.isoformat()
    )

    assert (
        cert["last_slot"]
        == last.isoformat()
    )

    assert (
        cert["historical_backfill"]
        is False
    )

    assert cert["gaps"] == 0


def test_failure_resets_current_streak(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    for i in range(81):

        if i == 40:
            make_attempt(
                tmp_path,
                T + i * fc.HOUR,
                status="FAILED",
            )

        else:
            make_attempt(
                tmp_path,
                T + i * fc.HOUR,
            )

    last = (
        T
        + 80 * fc.HOUR
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(last),
    )

    assert (
        report["failed_slots"]
        == 1
    )

    assert (
        report["current_streak"]
        == 40
    )

    assert (
        report["funding_81h_ready"]
        is False
    )

    assert (
        report["certificate"]
        is None
    )


def test_missing_middle_slot_is_preserved_gap(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    make_attempt(
        tmp_path,
        T,
    )

    make_attempt(
        tmp_path,
        T + 2 * fc.HOUR,
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(
            T + 2 * fc.HOUR
        ),
    )

    assert (
        report["successful_slots"]
        == 2
    )

    assert (
        report["missed_slots"]
        == 1
    )

    assert (
        report["current_streak"]
        == 1
    )

    assert len(
        report["gaps"]
    ) == 1

    assert (
        report["gaps"][0][
            "first_slot"
        ]
        == (
            T + fc.HOUR
        ).isoformat()
    )

    assert (
        report["gaps"][0][
            "statuses"
        ]
        == ["MISSED_SLOT"]
    )


def test_preactivation_attempt_never_counts(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    make_attempt(
        tmp_path,
        T - fc.HOUR,
    )

    make_attempt(
        tmp_path,
        T,
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report[
            "total_expected_slots"
        ]
        == 1
    )

    assert (
        report[
            "successful_slots"
        ]
        == 1
    )

    assert (
        report[
            "pre_activation_attempts"
        ]
        == 1
    )


def test_capture_before_target_is_invalid(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch,
        request_offsets={
            sid(T): 14,
        },
    )

    make_attempt(
        tmp_path,
        T,
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report["invalid_slots"]
        == 1
    )

    assert (
        report["successful_slots"]
        == 0
    )

    assert (
        report["current_streak"]
        == 0
    )


def test_capture_at_deadline_is_invalid(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch,
        request_offsets={
            sid(T): 120,
        },
    )

    make_attempt(
        tmp_path,
        T,
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report["invalid_slots"]
        == 1
    )

    assert (
        report["funding_81h_ready"]
        is False
    )


def test_receipt_identity_mismatch_is_invalid(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch,
        receipt_overrides={
            sid(T):
                "different-receipt"
        },
    )

    make_attempt(
        tmp_path,
        T,
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(T),
    )

    assert (
        report["invalid_slots"]
        == 1
    )

    assert (
        "identity mismatch"
        in report["records"][0][
            "reason"
        ]
    )


def test_certificate_set_hash_is_deterministic(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    for i in range(81):
        make_attempt(
            tmp_path,
            T + i * fc.HOUR,
        )

    last = (
        T
        + 80 * fc.HOUR
    )

    reference = (
        reference_after(last)
    )

    first = fc.status(
        tmp_path,
        T,
        reference,
    )

    second = fc.status(
        tmp_path,
        T,
        reference,
    )

    assert (
        first["certificate"][
            "certified_set_hash"
        ]
        == second["certificate"][
            "certified_set_hash"
        ]
    )


def test_structural_corruption_blocks_readiness(
    tmp_path,
    monkeypatch,
):
    install_fake_loader(
        monkeypatch
    )

    for i in range(81):
        make_attempt(
            tmp_path,
            T + i * fc.HOUR,
        )

    bad = (
        tmp_path
        / "attempts"
        / "not-a-slot"
    )

    bad.mkdir()

    last = (
        T
        + 80 * fc.HOUR
    )

    report = fc.status(
        tmp_path,
        T,
        reference_after(last),
    )

    assert (
        report["current_streak"]
        == 81
    )

    assert (
        report["invalid_slots"]
        == 1
    )

    assert (
        report["integrity"]
        == "FAIL"
    )

    assert (
        report["funding_81h_ready"]
        is False
    )

    assert (
        report["certificate"]
        is None
    )
