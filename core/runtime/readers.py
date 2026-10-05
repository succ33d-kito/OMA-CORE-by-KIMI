"""Configured local evidence readers. No network, initialization or remediation."""
from dataclasses import dataclass, replace
from pathlib import Path
import hashlib
import json
import sqlite3
from .contracts import DataSourceStatus, State, canonical, timestamp
from core.scientific import multi_market_capture as capture


@dataclass(frozen=True, slots=True)
class Source:
    name: str
    kind: str
    path: str
    node_id: str
    auxiliary: str | None = None
    max_age_seconds: int | None = None

    def __post_init__(self):
        if not all(type(v) is str and v for v in (self.name,self.kind,self.path,self.node_id)):
            raise ValueError('explicit source descriptor required')
        if self.max_age_seconds is not None and (type(self.max_age_seconds) is not int or self.max_age_seconds<0):
            raise ValueError('explicit nonnegative freshness limit required')


def read_json(path):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def sealed(path):
    data=read_json(path)
    if set(data)!={'payload','commitment'} or capture.commitment(data['payload'])!=data['commitment']:
        raise ValueError('commitment mismatch')
    return data['payload'],data['commitment']


def decision_summary(d):
    # Deliberately exclude raw content, future outcomes and legacy profitability.
    a=d['allocation']
    return dict(mode='SHADOW',decision_id=d['decision_id'],state=d['state'],
        world=dict(world_state_id=d['world']['world_state_id'],as_of=d['world']['as_of'],
                   markets=[m['symbol'] for m in d['world']['markets']]),
        radar=dict(radar_id=d['radar']['radar_id'],observed=d['radar']['observed'],
                   candidate_count=len(d['radar']['candidates']),candidates=[c['candidate_id'] for c in d['radar']['candidates']]),
        theses=[dict(thesis_id=t['thesis_id'],expression=t['expression']) for t in d['theses']],
        forecasts=[dict(forecast_id=f['forecast_id'],kind=f['kind'],calibration=f['calibration'],value=f['value']) for f in d['forecasts']],
        ranking=dict(ranking_id=a['ranking']['ranking_id'],label=a['ranking']['label'],ordered=a['ranking']['ordered']),
        portfolio=a['portfolio'],risk=[dict(authorization_id=r['authorization_id'],state=r['state'],reasons=r['reasons']) for r in a['authorizations']],
        allocation=dict(plan_id=a['plan_id'],unallocated=a['unallocated'],rows=[dict(candidate_id=r['candidate_id'],amount=r['amount'],reason=r['reason']) for r in a['rows']]))


def _read(source, at):
    path=Path(source.path)
    if source.kind=='price':
        from core.scientific.price_continuity import status
        if source.auxiliary is None or not Path(source.auxiliary).is_dir(): raise ValueError('Price state directory required')
        data=status(path,source.auxiliary,at,read_only=True)
        if data['ledger_integrity']!='PASS': raise ValueError('Price ledger verification failed')
        keys=('total_receipts','valid_price_receipts','current_streak','longest_streak','bars_to_81','regime_input_ready','ledger_integrity','last_receipt_at','last_valid_event_time')
        return {k:data[k] for k in keys},data['last_receipt_at'],data['ledger_head']
    if source.kind=='collector':
        data,digest=sealed(path)
        if set(data)!={'pid','status','next_expected_cycle','observed_at','integrity'} or data['status'] not in ('RUNNING','FAILED'):
            raise ValueError('unknown collector schema')
        timestamp(data['next_expected_cycle'])
        return dict(reported_status=data['status'],reported_pid=data['pid'],process_liveness='UNVERIFIED',
                    next_cycle=data['next_expected_cycle'],reported_integrity=data['integrity']),data['observed_at'],digest
    if source.kind in ('book','premium'):
        if source.auxiliary is None: raise ValueError('universe directory required')
        loader=capture.load_cycle
        if source.kind=='premium':
            from core.scientific.multi_market_premium import load_premium_cycle
            loader=load_premium_cycle
        cycle=loader(path,source.auxiliary)
        return dict(cycle_id=cycle.cycle_id,markets=[m.symbol for m in cycle.members],missing=list(cycle.missing),role='PILOT',
                    meaning='FUNDING_RATE_NOT_CASHFLOW' if source.kind=='premium' else 'BOOK_OBSERVATIONS'),cycle.completed_at.isoformat(),capture.commitment([m.observation_id for m in cycle.members])
    if source.kind in ('world','radar'):
        result=read_json(path/'result.json')
        world=read_json(path/'world.json'); radar=read_json(path/'radar.json')
        if capture.commitment(world)!=result['world_commitment'] or capture.commitment(radar)!=result['radar_commitment'] or radar['world_state_id']!=world['world_state_id']:
            raise ValueError('radar run integrity mismatch')
        if source.kind=='world':
            return dict(world_state_id=world['world_state_id'],markets=[m['symbol'] for m in world['markets']],role=world['role']),world['as_of'],result['world_commitment']
        return dict(radar_id=radar['radar_id'],observed=radar['observed'],missing=radar['missing'],candidate_count=len(radar['candidates']),
                    candidates=[dict(candidate_id=c['candidate_id'],status=c['status']) for c in radar['candidates']]),radar['generated_at'],result['radar_commitment']
    if source.kind=='shadow':
        from core.scientific.shadow_decision_ledger import _verify
        with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
            db.execute('BEGIN')
            _,head,_=_verify(db)
            rows=db.execute('SELECT body,recorded_at FROM shadow_entries ORDER BY seq DESC').fetchall()
        eligible=[(json.loads(body),recorded) for body,recorded in rows if timestamp(recorded)<=at]
        if not eligible: return dict(decision=None,mode='UNKNOWN'),None,head
        data,recorded=eligible[0]
        if timestamp(data['available_at'])>at: raise ValueError('future shadow decision')
        return decision_summary(data),data['available_at'],head
    if source.kind=='execution':
        saved=read_json(path); payload=saved['payload']
        if set(saved)!={'run_id','payload'} or capture.commitment(payload)!=saved['run_id'] or payload['version']!='WINDOW4R_SHADOW_INTENT_V0' or payload['mode']!='SHADOW':
            raise ValueError('invalid execution artifact')
        rows=[]; times=[]
        for r in payload['rows']:
            plan=r['plan']; decision=plan['decision']
            if decision['decision_id']!=payload['decision_id'] or plan['mode']!='SHADOW': raise ValueError('execution provenance mismatch')
            intent=r['intent']
            if intent is not None and intent['actionable'] is not False: raise ValueError('unexpected actionable intent')
            times.append(decision['available_at'])
            rows.append(dict(candidate_id=r['candidate_id'],status=r['status'],reason=r['reason'],plan_id=plan['plan_id'],
                gate=r['gate']['state'],intent_id=None if intent is None else intent['intent_id'],
                estimate=None,position_id=r['position_id'],lifecycle_assessment_id=r['lifecycle_assessment_id']))
        return dict(mode='SHADOW',upstream_state=payload['upstream_state'],rows=rows,execution='NO_EXECUTION_EVIDENCE'),max(times,key=timestamp) if times else None,saved['run_id']
    if source.kind=='position':
        read_json(path)  # Malformed configured artifacts must not hide as UNKNOWN.
        return dict(position=None,reason='NO_CANONICAL_POSITION_STORE_ADAPTER'),None,None
    raise ValueError('unsupported source kind')


def read_source(source, *, snapshot_at):
    at=timestamp(snapshot_at)
    ref=f'{source.node_id}/{source.name}'
    try:
        if not Path(source.path).exists():
            return DataSourceStatus(source.name,source=ref,reason='MISSING_SOURCE')
        details,source_at,digest=_read(source,at)
        if source_at is not None and timestamp(source_at)>at: raise ValueError('future source')
        state=State.AVAILABLE if digest else State.UNKNOWN
        freshness='UNKNOWN'
        if source_at is not None and source.max_age_seconds is not None:
            freshness='STALE' if (at-timestamp(source_at)).total_seconds()>source.max_age_seconds else 'CURRENT'
            if freshness=='STALE': state=State.STALE
        return DataSourceStatus(source.name,state,ref,source_at,digest,canonical(details),'VERIFIED_ARTIFACT_NOT_PROCESS_LIVENESS',freshness)
    except Exception as exc:
        return DataSourceStatus(source.name,State.INVALID,ref,reason='READ_OR_INTEGRITY_FAILURE:'+type(exc).__name__)
