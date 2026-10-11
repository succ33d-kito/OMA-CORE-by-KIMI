"""Regression: timestamp availability does not imply semantic eligibility."""
from datetime import timedelta
import pytest
from core.scientific.prospective_receipts import append_observation, is_causally_available
from core.scientific.causal_observation_snapshot import load_causal_snapshot
from core.scientific.causal_latent_context import project_latent_context
from core.scientific.causal_replay import replay_causal_state
from core.scientific.funding_rate_observation import append_verified_funding_rate_observation
from tests import test_funding_rate_observation as funding_fixture
from tests.test_metrics_continuity import S


@pytest.mark.parametrize('feature', ['Price/OHLCV', 'FundingRate/Published'])
def test_timestamp_and_hash_never_replace_semantic_evidence(tmp_path, feature):
    ledger = tmp_path/'ledger.db'
    row = append_observation(ledger, source='unverified', instrument='BTCUSDT',
        feature=feature, event_time=S, source_metric_at=S, received_at=S,
        payload={'funding_rate':'0.001'}, provenance={'contract':'unverified'}, clock=lambda:S)
    assert not is_causally_available(ledger,row['id'],S)
    before=ledger.read_bytes()
    snapshot=load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=S,features=(feature,))
    assert snapshot.observations == () and snapshot.missing_features == (feature,)
    assert ledger.read_bytes()==before


def test_verified_funding_remains_visible_and_historical_replay_stable(tmp_path,monkeypatch):
    monkeypatch.setattr(funding_fixture,'T',S)
    root,raw,received,available=funding_fixture.verified_capture(tmp_path)
    ledger=tmp_path/'ledger.db'
    admitted=S+timedelta(minutes=1)
    row=append_verified_funding_rate_observation(ledger,root,clock=lambda:admitted)
    assert is_causally_available(ledger,row['id'],admitted)
    earlier=load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=available)
    assert earlier.observations==()
    snapshot=load_causal_snapshot(ledger,instrument='BTCUSDT',as_of=admitted)
    assert [x.id for x in snapshot.observations]==[row['id']]
    assert project_latent_context(snapshot).context.funding_rate==float(raw['lastFundingRate'])
    first=replay_causal_state(ledger,tmp_path/'a.db',instrument='BTCUSDT',as_of=admitted)
    # A genuinely verified later receipt cannot alter the earlier reconstruction.
    monkeypatch.setattr(funding_fixture,'T',S+timedelta(minutes=2))
    root2,*_=funding_fixture.verified_capture(tmp_path,name='later')
    later=S+timedelta(minutes=3)
    row2=append_verified_funding_rate_observation(ledger,root2,clock=lambda:later)
    second=replay_causal_state(ledger,tmp_path/'b.db',instrument='BTCUSDT',as_of=admitted)
    assert first==second
    newest=replay_causal_state(ledger,tmp_path/'c.db',instrument='BTCUSDT',as_of=later)
    assert row2['id'] in newest.observation_ids and newest.replay_id!=first.replay_id
