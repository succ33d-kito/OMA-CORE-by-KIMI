from pathlib import Path
import hashlib
import json
import pytest
from scripts.check_mechanics_v2_1_freeze import DEFAULT, REPO, verify


def test_frozen_empty_subset_is_blocked_not_a_research_pass():
    result = verify()
    assert result['freeze_integrity'] == 'PASS'
    assert result['data_gate'] == 'FAIL'
    assert result['ready_hypotheses'] == 0
    assert result['blocked_hypotheses'] == 10
    assert not result['outcomes_read']


def test_tampered_freeze_rejected(tmp_path):
    p = tmp_path / 'FREEZE.json'
    p.write_bytes(DEFAULT.read_bytes() + b' ')
    p.with_suffix('.sha256').write_bytes(DEFAULT.with_suffix('.sha256').read_bytes())
    with pytest.raises(ValueError, match='hash mismatch'):
        verify(p, REPO)


def test_rehashed_missing_classification_rejected(tmp_path):
    d = json.loads(DEFAULT.read_text(encoding='utf-8'))
    d['issue_classification'].pop()
    body = json.dumps(d).encode()
    p = tmp_path / 'FREEZE.json'; p.write_bytes(body)
    p.with_suffix('.sha256').write_text(hashlib.sha256(body).hexdigest())
    with pytest.raises(ValueError, match='exactly one'):
        verify(p, REPO)
