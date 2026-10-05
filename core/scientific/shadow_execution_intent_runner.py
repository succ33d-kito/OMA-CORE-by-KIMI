"""Opt-in artifact runner. No HTTP, broker, scheduler, execution or fills."""
import json
from pathlib import Path

from . import execution_position_plane as plane
from . import trading_decision_plane as upstream
from .multi_market_capture import commitment, _write


def run_shadow_intents(decision, quality_policy, directory, *, enabled=False):
    if enabled is not True:
        raise ValueError('explicit shadow execution intent opt-in required')
    plane.verify(decision, upstream.ShadowCapitalDecision)
    plane.verify(quality_policy, plane.QualityPolicy)
    rows = []
    for row in sorted(decision.allocation.rows, key=lambda r:r.candidate_id):
        gate = plane.ExecutionQualityGate(decision,row.candidate_id,quality_policy)
        plan = plane.ExecutionPlan(decision,row.candidate_id,plane.Mode.SHADOW)
        intent = None
        if row.amount.value is None or row.amount.value <= 0:
            status, reason = row.reason, row.reason
        elif gate.state is not plane.QualityState.PASS:
            status, reason = gate.state.value, gate.reason
        elif plan.state is plane.PlanState.NO_ORDER:
            status, reason = 'NO_ORDER', plan.reason
        else:
            intent = plane.OrderIntent(plan)
            status, reason = 'NO_ORDER', intent.reason
        rows.append(dict(candidate_id=row.candidate_id,status=status,reason=reason,
            gate=upstream._plain(gate),plan=upstream._plain(plan),
            intent=None if intent is None else upstream._plain(intent),
            position_id=None,lifecycle_assessment_id=None))
    payload = dict(version='WINDOW4R_SHADOW_INTENT_V0',mode='SHADOW',role=decision.role,
        decision_id=decision.decision_id,upstream_state=decision.state.value,
        quality_policy_id=quality_policy.policy_id,rows=rows)
    run_id = commitment(payload)
    artifact = dict(run_id=run_id,payload=payload)
    raw = json.dumps(artifact,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    destination = directory / (run_id+'.json')
    try:
        _write(destination,raw)
    except FileExistsError:
        if destination.read_bytes() != raw:
            raise ValueError('conflicting or incomplete durable artifact; no overwrite') from None
    return artifact
