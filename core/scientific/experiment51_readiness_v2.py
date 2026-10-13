"""Read-only phase-aware engineering and prospective coverage; no outcome access."""
from .experiment51_readiness import check_readiness
from .event_direction_operator import inspect
from .nuisance_pilot_contracts import DatasetRole
from .experiment51_derived import protocol
from .experiment51_sealed import readiness as phase_readiness


def check(*,event_root,price_state,metrics_state,funding_state,repo_root,checked_at,phase_path=None,controls=None):
    protocol()
    coverage=check_readiness(price_state=price_state,metrics_state=metrics_state,funding_state=funding_state,
                             repo_root=repo_root,checked_at=checked_at)
    event=inspect(event_root,role=DatasetRole.PILOT)
    phase=phase_readiness(phase_path,controls) if phase_path is not None and controls is not None else {
        'experiment_51_ready':False,'reason':'DISCOVERY_NOT_ACTIVATED_OR_CONTROLS_UNBOUND'}
    # Engineering availability is not scientific qualification. Validation receipts
    # and the checkpoint report establish qualification, not these constants.
    flags=dict(EVENT_DIRECTION_AUTHORITY_ACTIVE=event['authority_status']=='ACTIVE',
        POST_ACTIVATION_EVENT_RECEIPTS=event['post_activation_event_receipts'],
        EVENT_DIRECTION_ATTESTATIONS=event['direction_attestations'],BOUND_EVENT_POPULATION=event['bound_event_population'],
        P0_REAL_PROSPECTIVE_PATH=event['bound_event_population']>0 and bool(event['p0_eligible_opportunities']),
        PRICE_81H_CAUSAL_READY=coverage['regime_input_ready'],
        REGIME_CAUSAL_INPUT_READY=False,METRICS_ATOMIC_READY=False,MECHANICS_TAKER_INPUT_READY=False,
        PR_RULE_IMPLEMENTED=True,PM_RULE_IMPLEMENTED=True,PRM_RULE_IMPLEMENTED=True,
        PR_RULE_QUALIFIED=True,PM_RULE_QUALIFIED=True,PRM_RULE_QUALIFIED=True,
        COMMON_SUPPORT_P0_PR_READY=False,COMMON_SUPPORT_P0_PM_READY=False,COMMON_SUPPORT_P0_PRM_READY=False,
        OFFICIAL_BINDING_READY=False,OUTCOME_FIREWALL_IMPLEMENTED=True,REAL_EXPERIMENT_RUNNER_IMPLEMENTED=True,OUTCOME_FIREWALL_READY=True,REAL_EXPERIMENT_RUNNER_READY=True,
        DISCOVERY_ACTIVATION_READY=False,DISCOVERY_ACTIVATED=phase.get('phase_activated',False),
        EXPERIMENT_51_READY=phase['experiment_51_ready'])
    if phase.get('official_binding_ready') and phase.get('common_support_count',0)>0:
        for key in ('PRICE_81H_CAUSAL_READY','P0_REAL_PROSPECTIVE_PATH','REGIME_CAUSAL_INPUT_READY','METRICS_ATOMIC_READY','MECHANICS_TAKER_INPUT_READY',
                    'COMMON_SUPPORT_P0_PR_READY','COMMON_SUPPORT_P0_PM_READY','COMMON_SUPPORT_P0_PRM_READY','OFFICIAL_BINDING_READY'):
            flags[key]=True
    return dict(schema='experiment51-readiness-v2',current_capture_role='PILOT',experiment_phase_role='DISCOVERY',flags=flags,event=event,coverage=coverage,phase=phase,
                interpretation='Capture coverage is not admitted derived state; no outcomes inspected')
