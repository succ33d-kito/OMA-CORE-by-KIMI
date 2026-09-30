"""Regression probes use synthetic data and real temporary SQLite records."""
import sqlite3
import pandas as pd
import pytest

from core.council.council import AgentCouncil
from core.schemas.knowledge_schema import KnowledgeStatus
from core.schemas.criterion_delta_schema import DeltaStatus
from core.schemas.outcome_comparison_schema import Verdict
from core.scientific.knowledge_lifecycle import extract_knowledge, promote_to_provisional, validate_knowledge
from core.scientific.criterion_evolution import propose_delta, apply_delta
from core.scientific.scientific_store import ScientificStore
from core.scientific.outcome_bridge import OutcomeBridge
from core.scientific.outcome_evaluator import auto_detect_verdict
from core.scientific.learning_integrity import LearningIntegrityError
from scripts.prospective_oi_taker_gate import window_available


@pytest.mark.parametrize('text', ['incorrect', 'invalid', 'not confirmed', 'not valid', 'never increased', 'confirmed but wrong'])
def test_negative_text_cannot_confirm(text):
    assert auto_detect_verdict(text, 'bullish')[0] != Verdict.CONFIRMED


def test_unknown_or_negated_numeric_outcome_is_not_confirmation():
    from core.scientific.outcome_comparison import auto_detect_verdict as compare
    assert auto_detect_verdict('uninterpretable observation', 'neutral')[0] == Verdict.INCONCLUSIVE
    assert compare('price will rise 3%', 'price did not rise 3%') == Verdict.INCONCLUSIVE


def test_council_ema_bounded_and_recovers_legacy_corruption():
    council = AgentCouncil()
    for _ in range(1000):
        council.update_track_record('a', True)
        assert 0 <= council.get_track_record('a') <= 1
    for _ in range(1000):
        council.update_track_record('a', False)
        assert 0 <= council.get_track_record('a') <= 1
    for invalid in [1.5, -0.1, float('nan'), float('inf')]:
        council._track_record['a'] = invalid
        assert council.get_track_record('a') == .5
        council.update_track_record('a', True)
        assert council.get_track_record('a') == .55
    with pytest.raises(ValueError):
        council.update_track_record('a', 1)


@pytest.mark.parametrize('index', [0, 40, 80])
def test_every_feature_bar_requires_timely_receipt(index):
    decision = pd.Timestamp('2024-01-05', tz='UTC')
    available = pd.Series(pd.date_range(end=decision, periods=81, freq='h'))
    assert window_available(available, decision)
    available.iloc[index] = decision + pd.Timedelta(seconds=1)
    assert not window_available(available, decision)
    available.iloc[index] = pd.NaT
    assert not window_available(available, decision)
    assert not window_available(available.iloc[1:], decision)


def test_bridge_reads_sqlite_rows_without_mutating_source(tmp_path):
    operational = tmp_path / 'operational.db'
    names = 'id event_id title description opportunity_type asset_class assets score conviction priority action_suggested risk_level timestamp expires_at status'.split()
    with sqlite3.connect(operational) as conn:
        conn.execute('CREATE TABLE opportunities (' + ','.join(n + (' REAL' if n in ['score','conviction'] else ' TEXT') for n in names) + ')')
        row = ['o','e','BTC','test','LONG_SETUP','crypto','["BTC"]',85.,75.,'HIGH','observe','MEDIUM','2024-01-01','2024-01-02','active']
        conn.execute('INSERT INTO opportunities VALUES (' + ','.join('?' for _ in names) + ')', row)
    before = operational.read_bytes()
    bridge = OutcomeBridge(str(operational), str(tmp_path / 'scientific.db'))
    assert bridge.fetch_opportunities(min_score=80)[0]['id'] == 'o'
    assert bridge.fetch_opportunities(min_score=90) == []
    assert bridge.bridge_all(dry_run=True)['hypotheses_generated'] == 1
    assert operational.read_bytes() == before


def test_promotion_and_store_bypasses_fail_closed(tmp_path):
    store = ScientificStore(str(tmp_path / 'science.db'))
    k = extract_knowledge('candidate', [], [], '', '', '', '')
    store.create_knowledge(k)
    assert store.get_knowledge(k.id).provenance['learning_eligible'] is False
    promote_to_provisional(k)
    store.update_knowledge(k)
    with pytest.raises(LearningIntegrityError):
        validate_knowledge(k)
    assert k.status == KnowledgeStatus.PROVISIONAL
    assert k.last_validated_at is None
    k.status = KnowledgeStatus.VALIDATED
    k.replication_count = 999  # Caller claims are not independently verified evidence.
    for operation in [store.create_knowledge, store.update_knowledge]:
        with pytest.raises(LearningIntegrityError):
            operation(k)
    assert store.get_knowledge(k.id).status == KnowledgeStatus.PROVISIONAL
    d = propose_delta([k.id], [], [], 'calibration', 'unproven change')
    store.create_criterion_delta(d)
    with pytest.raises(LearningIntegrityError):
        apply_delta(d)
    assert d.applied_at is None
    d.status = DeltaStatus.APPLIED
    for operation in [store.create_criterion_delta, store.update_criterion_delta]:
        with pytest.raises(LearningIntegrityError):
            operation(d)
    assert store.get_criterion_delta(d.id).status == DeltaStatus.PENDING_REVIEW
