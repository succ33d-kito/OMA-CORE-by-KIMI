import pytest
from core.scientific import experiment51_readiness_v2 as r


@pytest.mark.parametrize('phase_ready',[False,True])
def test_synthetic_phase_flags_never_open_outcomes(monkeypatch,phase_ready):
    monkeypatch.setattr(r,'check_readiness',lambda **kw:{'regime_input_ready':False})
    monkeypatch.setattr(r,'inspect',lambda *a,**kw:dict(authority_status='ACTIVE',post_activation_event_receipts=0,
        direction_attestations=0,bound_event_population=0,p0_eligible_opportunities=0))
    monkeypatch.setattr(r,'phase_readiness',lambda *a:dict(experiment_51_ready=phase_ready,phase_activated=True,
        official_binding_ready=phase_ready,common_support_count=200 if phase_ready else None))
    result=r.check(event_root='fixture',price_state='fixture',metrics_state='fixture',funding_state='fixture',
        repo_root='fixture',checked_at=None,phase_path='fixture',controls='fixture')
    assert result['flags']['EXPERIMENT_51_READY'] is phase_ready
    assert result['flags']['COMMON_SUPPORT_P0_PR_READY'] is phase_ready
    assert result['flags']['PRICE_81H_CAUSAL_READY'] is phase_ready
    assert result['current_capture_role']=='PILOT' and result['experiment_phase_role']=='DISCOVERY'
