from datetime import timedelta
from dataclasses import FrozenInstanceError
import pytest
from core.scientific import experiment51_derived as e
from core.scientific.decision_rule import IntentAction as A
from tests.test_role_price_window import window
from core.scientific.role_price_window import certify_role_price_window
from core.scientific.causal_regime import append_causal_regime
from core.scientific.causal_mechanics import append_causal_mechanics


@pytest.mark.parametrize('base',list(A))
@pytest.mark.parametrize('structure',['trend','range','transition','unknown',None])
@pytest.mark.parametrize('taker',[None,'0.5','1','1.5'])
def test_frozen_policy_matrix(base,structure,taker):
    # IntentAction is a closed LONG/SHORT/ABSTAIN vocabulary.
    result=e.actions(base,structure,taker)
    assert result[0][0] is base
    for action,_ in result:
        assert action in (base,A.ABSTAIN)
    assert (result[1][0] is base) if base is A.ABSTAIN else (result[1][0] is base)==(structure in ('trend','range'))
    confirmation=(base is A.LONG and taker=='1.5') or (base is A.SHORT and taker=='0.5')
    assert result[2][0] is (base if confirmation else A.ABSTAIN)
    assert result[3][0] is (base if confirmation and structure in ('trend','range') else A.ABSTAIN)


@pytest.mark.parametrize('bad',['NaN','Infinity','-1'])
def test_bad_taker_is_invalid_not_abstention(bad):
    with pytest.raises(ValueError): e.actions(A.LONG,'trend',bad)


def test_regime_exact_replay(window):
    ledger,ids,cutoff,_=window
    cert=certify_role_price_window(ledger,receipt_ids=ids,dataset_role='PILOT',cutoff=cutoff)
    row=append_causal_regime(ledger,cert,clock=lambda:cutoff+timedelta(seconds=1))
    D=cutoff.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
    first=e.derived(ledger,role='PILOT',decision_at=D,regime_id=row['id'])
    assert first==e.derived(ledger,role='PILOT',decision_at=D,regime_id=row['id'])
    assert len(first.dependencies)==162
    with pytest.raises(FrozenInstanceError): first.structure='trend'
    for role,decision in [('DISCOVERY',D),('PILOT',D+timedelta(hours=1)),('PILOT',cutoff)]:
        with pytest.raises(ValueError): e.derived(ledger,role=role,decision_at=decision,regime_id=row['id'])


def test_missing_mechanics_bundle_fails(window):
    ledger,ids,cutoff,_=window
    row=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=cutoff,clock=lambda:cutoff)
    D=cutoff.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
    with pytest.raises(ValueError,match='INVALID_BUNDLE'): e.derived(ledger,role='PILOT',decision_at=D,mechanics_id=row['id'])


def test_protocol_hash_gate(monkeypatch):
    monkeypatch.setattr(e,'load_protocol',lambda:{})
    with pytest.raises(ValueError): e.protocol()


from tests.test_metrics_continuity import state,S
from tests.test_causal_latent_context import admit_metrics


@pytest.mark.skipif(__import__('os').name!='nt',reason='Existing Metrics activation fixture requires Windows; verified in local focal suite')
def test_authenticated_atomic_taker(state,tmp_path):
    ledger=tmp_path/'metrics.db';admit_metrics(state,ledger)
    cutoff=S+timedelta(minutes=5)
    row=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=cutoff,clock=lambda:cutoff)
    view=e.derived(ledger,role='PILOT',decision_at=S+timedelta(hours=1),mechanics_id=row['id'])
    assert view.taker=='1.4' and len(view.dependencies)==6
    assert e.actions(A.LONG,None,view.taker)[2][0] is A.LONG
    with pytest.raises(ValueError): e.derived(ledger,role='DISCOVERY',decision_at=S+timedelta(hours=1),mechanics_id=row['id'])


@pytest.mark.skipif(__import__('os').name!='nt',reason='Existing atomic Metrics activation fixture is Windows-only')
def test_four_arm_authenticated_reconstruction(state,tmp_path,monkeypatch):
    import tests.test_price_role_attestation as pricefixture
    from tests.test_real_event_receipt import setup_store,evidence
    from tests.test_event_direction_v1 import claim,controls
    from core.scientific.event_direction_v1 import EventDirectionAuthority
    from core.scientific.nuisance_pilot_contracts import DatasetRole
    from core.scientific import real_event_receipt as ev
    monkeypatch.setattr(pricefixture,'T',S-timedelta(hours=80))
    ledger,ids,cutoff,_=window.__wrapped__(tmp_path,monkeypatch)
    cert=certify_role_price_window(ledger,receipt_ids=ids,dataset_role='PILOT',cutoff=cutoff)
    regime=append_causal_regime(ledger,cert,clock=lambda:cutoff+timedelta(seconds=1))
    admit_metrics(state,ledger)
    mech=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=S+timedelta(minutes=5),clock=lambda:S+timedelta(minutes=5))
    store,clock=setup_store(tmp_path,monkeypatch)
    D=S+timedelta(hours=1);clock['now']=D-timedelta(minutes=40)
    authority=EventDirectionAuthority.activate(tmp_path/'direction.sqlite',role=DatasetRole.PILOT)
    clock['now']=D-timedelta(minutes=20);clock['raw']=b'Bitcoin announcement. Actor commits to Bitcoin action.'
    receipt=store.capture('official','v1',DatasetRole.PILOT);store.admit(receipt.receipt_id,evidence())
    authority.attest(store,receipt.receipt_id,claim());clock['now']=D;store.close(D)
    result=e.reconstruct(authority,store,receipt.receipt_id,controls(),ledger=ledger,regime_id=regime['id'],mechanics_id=mech['id'])
    op,kernel,support,bodies,view=result
    assert support.cs4 and {body['action'] for body in bodies}=={'ABSTAIN'}
    assert len({body['opportunity_id'] for body in bodies})==1
    assert e.reconstruct(authority,store,receipt.receipt_id,controls(),ledger=ledger,regime_id=regime['id'],mechanics_id=mech['id'])==result
    assert bodies[0]['regime_id'] is None and bodies[0]['mechanics_id'] is None
    assert bodies[1]['mechanics_id'] is None and bodies[2]['regime_id'] is None
