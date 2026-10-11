from copy import deepcopy
from datetime import timedelta
import pytest
import tests.test_price_role_attestation as fixture
from core.scientific import price_role_attestation as attestation
from core.scientific.prospective_receipts import observation_snapshot
from core.scientific.role_price_window import _build, certify_role_price_window, verify_role_price_window


@pytest.fixture
def window(tmp_path, monkeypatch):
    start = fixture.T
    state = fixture.create_activation(tmp_path, monkeypatch)
    ledger = tmp_path / "window.db"
    ids = []
    for hour in range(81):
        t = start + timedelta(hours=hour)
        monkeypatch.setattr(fixture, "T", t)
        auth = fixture.authorize(state, monkeypatch)
        row = fixture.append_price(ledger)
        monkeypatch.setattr(attestation, "_now", lambda t=t: t+timedelta(seconds=4))
        attestation.attest_price_observation(state, ledger, repo_root=fixture.repo_root(),
            slot_id=auth["slot_id"], observation_id=row["id"])
        ids.append(row["id"])
    cutoff = t+timedelta(seconds=5)
    known, _ = observation_snapshot(ledger, read_only=True)
    return ledger, ids, cutoff, known


def test_certificate_and_reconstruction(window):
    ledger, ids, cutoff, known = window
    cert = certify_role_price_window(ledger, receipt_ids=ids, dataset_role="PILOT", cutoff=cutoff)
    assert verify_role_price_window(ledger, cert) == cert
    assert cert == _build(dict(reversed(list(known.items()))), ids, "PILOT", cutoff)
    assert len(cert["attestation_ids"]) == 81
    for key, value in (("dataset_role", "DISCOVERY"), ("price_commitment", "fake"), ("certificate_id", "fake")):
        altered = {**cert, key: value}
        with pytest.raises(ValueError):
            verify_role_price_window(ledger, altered)


def test_invalid_windows_and_roles(window):
    _, ids, cutoff, known = window
    for bad in (ids[:80], ids+[ids[0]], ids[:-1]+[ids[0]], list(reversed(ids))):
        with pytest.raises(ValueError):
            _build(known, bad, "PILOT", cutoff)
    for role in (None, "UNKNOWN", "DISCOVERY", "CONFIRMATION"):
        with pytest.raises(ValueError):
            _build(known, ids, role, cutoff)
    with pytest.raises(ValueError):
        _build(known, ids, "PILOT", cutoff.replace(tzinfo=None))
    with pytest.raises(ValueError):
        _build(known, ids, "PILOT", cutoff-timedelta(seconds=2))


def test_dependency_tampering_and_conflicts(window):
    _, ids, cutoff, known = window
    cert = _build(known, ids, "PILOT", cutoff)
    aid = cert["attestation_ids"][30]
    changes = [(aid, None), (ids[30], None), (ids[30], {**known[ids[30]], "instrument": "ETHUSDT"})]
    bad_att = deepcopy(known[aid])
    bad_att["payload"]["dataset_role"] = "CONFIRMATION"
    changes.append((aid, bad_att))
    for identity, replacement in changes:
        altered = dict(known)
        if replacement is None:
            del altered[identity]
        else:
            altered[identity] = replacement
        with pytest.raises(ValueError):
            _build(altered, ids, "PILOT", cutoff)
    duplicate = {**known[ids[30]], "id": "conflicting"}
    with pytest.raises(ValueError):
        _build({**known, "conflicting": duplicate}, ids, "PILOT", cutoff)
    future = {**duplicate, "available_at": (cutoff+timedelta(hours=1)).isoformat()}
    assert _build({**known, "conflicting": future}, ids, "PILOT", cutoff) == cert
