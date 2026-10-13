"""Create-once phase/population/run commitments. Outcome callback only after gates.

Local filesystem custody and explicit owner authorization remain trust boundaries.
This module does not activate phases automatically or capture/repair evidence.
"""
from datetime import datetime, timedelta
from pathlib import Path
import json
import sqlite3
from statistics import mean
from . import real_event_receipt as events
from . import event_direction_operator as operator
from .experiment51_derived import reconstruct, protocol, FAMILY, RULES, PREREG
from .experiment51_preparation import _paired, _basic_intervals
from .nuisance_pilot_contracts import DatasetRole, digest
from .experimental_manifest import PopulationScope, PopulationManifestBuilder
from .official_manifest_binding import OfficialManifestStore
from .regime_observation import _utc

HOUR=timedelta(hours=1)
_OUTCOME_KEY=object()


class _OutcomePermit:
    __slots__=('key',)
    def __init__(self,key):
        if key is not _OUTCOME_KEY: raise ValueError('OUTCOME_ACCESS_NOT_AUTHORIZED')
        self.key=key


def activate_phase(path, *, operator_root, ledger, controls, owner_authorization):
    """Explicit owner operation, DISCOVERY only; no caller clock/start time."""
    protocol()
    if type(owner_authorization) is not str or not owner_authorization.strip():
        raise ValueError('EXPLICIT_OWNER_AUTHORIZATION_REQUIRED')
    _,authority,store,_,binding=operator._open(operator_root,DatasetRole.DISCOVERY)
    now=events._now(); start=now.replace(minute=0,second=0,microsecond=0)+HOUR
    config=dict(schema='experiment51-phase-v1',role='DISCOVERY',prereg=PREREG,rules=list(RULES),family=FAMILY,
        owner_authorization=owner_authorization,operator_root=str(Path(operator_root).resolve()),
        authority_id=authority.authority_id,activation_id=digest(binding),ledger=str(Path(ledger).resolve()),
        controls_id=controls.identity,start=start.isoformat(),end=(start+2160*HOUR).isoformat())
    path=Path(path)
    with path.open('xb'): pass
    journal=events.RealEventStore(path)
    journal._append('phase',config,lambda rows,at:None)
    return _phase(path,controls)[2]


def _phase(path,controls,*,write=False):
    protocol()
    journal=events.RealEventStore(path,read_only=not write);rows=journal._rows()
    if not rows or rows[0]['kind']!='phase': raise ValueError('PHASE_MISSING')
    p=rows[0]['data']
    if (p['schema']!='experiment51-phase-v1' or p['role']!='DISCOVERY' or p['prereg']!=PREREG
            or p['rules']!=list(RULES) or p['family']!=FAMILY or p['controls_id']!=controls.identity
            or not _utc(rows[0]['at'])<_utc(p['start']) or _utc(p['end'])-_utc(p['start'])!=2160*HOUR):
        raise ValueError('PHASE_ROLE_RULE_OR_PROTOCOL_MISMATCH')
    _,authority,store,_,binding=operator._open(p['operator_root'],DatasetRole.DISCOVERY)
    if authority.authority_id!=p['authority_id'] or digest(binding)!=p['activation_id']:
        raise ValueError('EVENT_AUTHORITY_MISMATCH')
    return journal,rows,p,authority,store


def _member(p,op):
    # First full H1 starts strictly after D; maximum label must remain inside phase.
    return _utc(p['start'])<=op.decision_at and op.decision_at+9*HOUR<=_utc(p['end'])


def record_opportunity(path,controls,receipt_id,*,regime_id=None,mechanics_id=None):
    journal,rows,p,authority,store=_phase(path,controls,write=True)
    if store is None: raise ValueError('EVENT_POPULATION_MISSING')
    record=operator._record(authority,store,receipt_id,_utc(operator._open(p['operator_root'],DatasetRole.DISCOVERY)[4]['at']))
    op,decisions,support,bodies,view=reconstruct(authority,store,receipt_id,controls,ledger=p['ledger'],
        regime_id=regime_id,mechanics_id=mechanics_id)
    if not _member(p,op): raise ValueError('PHASE_BOUNDARY_PURGE')
    body=dict(receipt_id=receipt_id,opportunity_id=op.opportunity_id,regime_id=regime_id,mechanics_id=mechanics_id,
              policies=list(bodies),support_id=support.support_id,cs4=support.cs4,derived_id=view.commitment)
    old=[r for r in rows if r['kind']=='decision' and r['data']['opportunity_id']==op.opportunity_id]
    if old:
        if len(old)!=1 or old[0]['data']!=body: raise ValueError('DECISION_CONFLICT')
        return digest(old[0])
    def check(current,at):
        if any(r['kind'] in ('binding','authorized_run') for r in current): raise ValueError('FROZEN')
        if any(r['kind']=='decision' and r['data']['opportunity_id']==op.opportunity_id for r in current): raise ValueError('DUPLICATE')
        if not op.decision_at<=at<op.decision_at+4*HOUR: raise ValueError('LATE_POLICY_FORMATION')
    journal._append('decision',body,check)
    return digest(journal._rows()[-1])


def _rebuild(rows,p,authority,store,controls):
    if store is None: raise ValueError('EVENT_POPULATION_MISSING')
    if not any(r['kind']=='close' and _utc(r['data']['cutoff'])>=_utc(p['end']) for r in store._rows()):
        raise ValueError('EVENT_PHASE_NOT_CLOSED')
    population=store.population()
    members=tuple(o for o in population if _member(p,o))
    if not members: raise ValueError('EMPTY_POPULATION')
    decisions={}
    for row in rows:
        if row['kind']=='decision':
            oid=row['data']['opportunity_id']
            if oid in decisions: raise ValueError('DUPLICATE_DECISION')
            decisions[oid]=row
    if set(decisions)!={o.opportunity_id for o in members}: raise ValueError('EXACT_POPULATION_MISMATCH')
    prepared=[]
    for original in sorted(members,key=lambda o:o.opportunity_id):
        saved=decisions[original.opportunity_id];data=saved['data']
        operator._record(authority,store,data['receipt_id'],_utc(operator._open(p['operator_root'],DatasetRole.DISCOVERY)[4]['at']))
        op,kernel,support,bodies,view=reconstruct(authority,store,data['receipt_id'],controls,ledger=p['ledger'],
            regime_id=data['regime_id'],mechanics_id=data['mechanics_id'])
        expected=dict(receipt_id=data['receipt_id'],opportunity_id=op.opportunity_id,regime_id=data['regime_id'],
                      mechanics_id=data['mechanics_id'],policies=list(bodies),support_id=support.support_id,
                      cs4=support.cs4,derived_id=view.commitment)
        if data!=expected or not op.decision_at<=_utc(saved['at'])<op.decision_at+4*HOUR:
            raise ValueError('POLICY_OR_DERIVED_OR_SUPPORT_MISMATCH')
        prepared.append((op,kernel,support,bodies))
    population_id=digest(tuple((o.opportunity_id,o.event_id,o.event_cluster_id) for o in sorted(population,key=lambda o:o.opportunity_id)))
    return prepared,population_id


def _manifest(prepared,p,frozen):
    first=prepared[0][0]
    scope=PopulationScope(first.protocol_id,first.protocol_hash,first.run_id,first.dataset_role,first.population_rule_hash,_utc(p['end']))
    builder=PopulationManifestBuilder(scope)
    for op,kernel,support,_ in prepared: builder.add(op,kernel[0].controls,kernel,support)
    return builder.freeze(frozen)


def bind_experiment(path,controls):
    journal,rows,p,authority,store=_phase(path,controls,write=True)
    if any(r['kind'] in ('binding','authorized_run') for r in rows): raise ValueError('ALREADY_FROZEN')
    now=events._now()
    if now<_utc(p['end']): raise ValueError('PHASE_INCOMPLETE')
    prepared,population_id=_rebuild(rows,p,authority,store,controls)
    manifest=_manifest(prepared,p,now)
    directory=Path(str(path)+'.official')
    official=OfficialManifestStore(directory).bind(manifest.scope,manifest,now)
    manifest_path=directory/'manifest.json';manifest.write_exclusive(manifest_path)
    cs=tuple(op.opportunity_id for op,_,support,_ in prepared if support.cs4)
    body=dict(prereg=PREREG,rules=list(RULES),phase_id=digest(rows[0]),event_population_id=population_id,
              manifest=manifest.to_json(),official=official.to_json(),
              support={name:list(cs) for name in ('PR-P0','PM-P0','PRM-P0')},
              support_id=digest((FAMILY,cs)),frozen_at=now.isoformat())
    journal._append('binding',body,lambda current,at:None)
    return digest(journal._rows()[-1])


def _gates(path,controls):
    journal,rows,p,authority,store=_phase(path,controls)
    bindings=[r for r in rows if r['kind']=='binding']
    if len(bindings)!=1: raise ValueError('OFFICIAL_BINDING_MISSING')
    b=bindings[0]['data']
    if b['prereg']!=PREREG or b['rules']!=list(RULES) or b['phase_id']!=digest(rows[0]): raise ValueError('BINDING_MISMATCH')
    prepared,population_id=_rebuild(rows,p,authority,store,controls)
    manifest=_manifest(prepared,p,_utc(b['frozen_at']))
    cs=tuple(op.opportunity_id for op,_,support,_ in prepared if support.cs4)
    if (b['event_population_id']!=population_id or b['manifest']!=manifest.to_json()
            or b['support']!={name:list(cs) for name in ('PR-P0','PM-P0','PRM-P0')}
            or b['support_id']!=digest((FAMILY,cs))): raise ValueError('POPULATION_OR_SUPPORT_MISMATCH')
    official=json.loads(b['official']);directory=Path(str(path)+'.official')
    if ((directory/(official['scope_id']+'.json')).read_text()!=b['official']+'\n'
            or (directory/'manifest.json').read_text()!=b['manifest']+'\n'
            or official['manifest_content_digest']!=digest(b['manifest'])): raise ValueError('OFFICIAL_BINDING_TAMPERED')
    selected=[item for item in prepared if item[2].cs4]
    active=[sum(item[3][i]['action']!='ABSTAIN' for item in selected) for i in range(4)]
    blocks={int((op.decision_at-_utc(p['start'])).total_seconds()//(168*3600)) for op,_,_,_ in selected}
    ready=(not any(r['kind']=='authorized_run' for r in rows) and events._now()>=_utc(p['end'])+8*HOUR and len(cs)>=200 and min(active,default=0)>=200 and len(blocks)>=12)
    return rows,p,selected,ready


def readiness(path,controls):
    """No writes, no labels; errors remain explicit, never promote partial evidence."""
    activated=False
    try:
        _phase(path,controls)
        activated=True
        _,_,selected,ready=_gates(path,controls)
        return dict(experiment_51_ready=ready,phase_activated=True,official_binding_ready=True,common_support_count=len(selected),reason=None if ready else 'INSUFFICIENT_SUPPORT_MATURATION_OR_RUN_ALREADY_ATTEMPTED')
    except (ValueError,KeyError,TypeError,OSError,sqlite3.Error) as error:
        return dict(experiment_51_ready=False,phase_activated=activated,official_binding_ready=False,common_support_count=None,reason=str(error))


def run(path,controls,*,outcome_loader=None):
    rows,p,selected,ready=_gates(path,controls)
    if not ready: raise ValueError('READINESS_FALSE')
    if any(r['kind']=='authorized_run' for r in rows): raise ValueError('RUN_ALREADY_ATTEMPTED')
    identity=digest((digest(rows[0]),digest(next(r for r in rows if r['kind']=='binding')),RULES))
    journal=events.RealEventStore(path)
    def check(current,at):
        if current!=rows: raise ValueError('STATE_CHANGED')
    journal._append('authorized_run',dict(run_id=identity),check)
    # OUTCOME FIREWALL: no loader call exists above this line.
    loader=outcome_loader if outcome_loader is not None else lambda run_id,population,horizons: _load_labels(p['ledger'],population,horizons,permit=_OutcomePermit(_OUTCOME_KEY))
    labels=loader(identity,tuple((o.opportunity_id,o.decision_at.isoformat()) for o,_,_,_ in selected),(1,4,8))
    result=_analyze(p,selected,labels,identity)
    result['evidence_kind']='INJECTED_NOT_REAL' if outcome_loader is not None else 'ROLE_AUTHENTICATED_PRICE_LABELS'
    return result


def _analyze(phase,selected,labels,run_id):
    """Statistical core; labels are simple returns from the frozen next-full-H1 windows.

    Loader must authenticate its label source; this API never discovers/down-loads data.
    """
    spec=protocol();ids=tuple(o.opportunity_id for o,_,_,_ in selected)
    if set(labels)!=set(ids): raise ValueError('LABEL_POPULATION_MISMATCH')
    results={}
    for horizon in (4,1,8):
        arms={name:{} for name in ('P0','PR','PM','PRM')}
        for op,_,_,bodies in selected:
            item=labels[op.opportunity_id]
            if set(item)!={1,4,8}: raise ValueError('LABEL_HORIZON_MISMATCH')
            value=item[horizon]
            if type(value) not in (int,float) or not __import__('math').isfinite(value): raise ValueError('INVALID_LABEL')
            for body in bodies:
                action={'LONG':1,'SHORT':-1,'ABSTAIN':0}[body['action']]
                arms[body['policy']][op.opportunity_id]=10000*action*value-(10 if action else 0)
        pairs=_paired(ids,arms);calendar=[[] for _ in range(2160)]
        for i,(op,_,_,_) in enumerate(selected):
            hour=int((op.decision_at-_utc(phase['start'])).total_seconds()//3600)
            calendar[hour].append(tuple(pairs[n][i] for n in ('PR','PM','PRM')))
        intervals=_basic_intervals(calendar,spec['uncertainty'])
        results[horizon]={name:dict(mean_bps=mean(pairs[name]),interval=interval,
            verdict='INCONCLUSIVE' if interval is None else 'PASS' if interval[0]>2 else 'FAIL' if interval[1]<=2 else 'INCONCLUSIVE')
            for name,interval in zip(('PR','PM','PRM'),intervals)}
    return dict(run_id=run_id,primary=results[4],exploratory={h:results[h] for h in (1,8)},
                policy_winner=None,edge='NOT_DEMONSTRATED',confirmation_required=True)


def _load_labels(ledger,population,horizons,*,permit=None):
    """Outcome-side adapter: call only after run authorization, never in readiness."""
    if type(permit) is not _OutcomePermit or permit.key is not _OUTCOME_KEY:
        raise ValueError('OUTCOME_ACCESS_NOT_AUTHORIZED')
    from decimal import Decimal
    from .prospective_receipts import observation_snapshot,snapshot_causally_available
    from .price_role_attestation import verified_price_role_attestation
    if tuple(horizons)!=(1,4,8): raise ValueError('FROZEN_HORIZONS_REQUIRED')
    known,_=observation_snapshot(ledger,read_only=True);now=events._now();labels={}
    for identity,decision in population:
        entry=_utc(decision)+HOUR
        bars=[]
        for offset in range(1,9):
            slot=entry+offset*HOUR
            candidates=[r for r in known.values() if r['feature']=='Price/OHLCV' and r['instrument']=='BTCUSDT' and _utc(r['event_time'])==slot]
            if len(candidates)!=1: raise ValueError('LABEL_MISSING_OR_CONFLICTING_PRICE')
            raw=candidates[0]
            if (not snapshot_causally_available(known,raw['id'],now)
                    or verified_price_role_attestation(known,raw,'DISCOVERY',now) is None):
                raise ValueError('LABEL_ROLE_OR_PROVENANCE_FAILURE')
            bars.append(raw)
        opened=Decimal(str(bars[0]['payload']['open']))
        if not opened.is_finite() or opened<=0: raise ValueError('INVALID_LABEL_OPEN')
        labels[identity]={h:float(Decimal(str(bars[h-1]['payload']['close']))/opened-1) for h in horizons}
    return labels
