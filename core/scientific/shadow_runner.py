"""Reference-only prospective shadow pipeline. No capture, broker, or scheduling."""
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from . import trading_decision_plane as t
from . import multi_market_capture as c
from .multi_market_premium import load_premium_cycle
from .radar_runner import load_config as load_radar_config
from .coverage_ledger import load_masks
from .world_state import load_world,WorldMarket
from .data_quality import DataQuality
from .opportunity_radar import scan


def freeze_shadow_config(directory,universe_directory,radar_config_directory,ranking_policy_directory,mask_directory,*,
                         mask_name,risk_policy,allocation_policy,equity,budget,requested_risk,kill_switch):
    u=c.load_universe(universe_directory); radar=load_radar_config(radar_config_directory,universe_directory)
    ranking=t.load_ranking_policy(ranking_policy_directory); masks=load_masks(mask_directory,universe_directory)
    mask=next((m for m in masks if m.name==mask_name),None)
    if mask is None or type(risk_policy) is not t.RiskPolicy or type(allocation_policy) is not t.AllocationPolicy: raise ValueError('frozen mask/risk/allocation required')
    if any(type(x) is not t.CapitalAmount for x in (equity,budget,requested_risk)) or equity.unit is not t.CapitalUnit.USD_NOTIONAL: raise TypeError('explicit shadow capital required')
    if kill_switch is not None and type(kill_switch) is not bool: raise TypeError('explicit kill switch required')
    now=c._now()
    if any(at>now for at in (radar.frozen_at,ranking.registered_at,mask.frozen_at,risk_policy.registered_at,allocation_policy.registered_at)): raise ValueError('future config dependency')
    params=dict(universe_id=u.universe_id,radar_id=radar.config_id,ranking_id=ranking.policy_id,mask_id=mask.mask_id,mask_name=mask_name,
        risk=t._plain(risk_policy),allocation=t._plain(allocation_policy),equity=t._plain(equity),budget=t._plain(budget),
        requested_risk=t._plain(requested_risk),kill_switch=kill_switch,role='PILOT',thesis_policy='REFERENCE_NON_VALIDATED_v0',forecast_producer='UNKNOWN_DIRECTION_v0')
    root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    c._write(root/'parameters.json',c._json(params))
    payload=dict(parameters=params,frozen_at=c._now().isoformat())
    c._write(root/'config.json',c._json(dict(payload=payload,commitment=c.commitment(payload))))
    return c.commitment(payload)


def _amount(value): return t.CapitalAmount(t.CapitalUnit(value['unit']),None if value['value'] is None else Decimal(value['value']))


def _policies(params):
    risk=dict(params['risk']); rid=risk.pop('policy_id')
    risk['registered_at']=datetime.fromisoformat(risk['registered_at']); risk['unit']=t.CapitalUnit(risk['unit'])
    for k in ('position_limit','aggregate_limit','max_age_seconds'):
        risk[k]=None if risk[k] is None else Decimal(risk[k])
    risk['required_future_controls']=tuple(t.FutureRiskControl(v) for v in risk['required_future_controls'])
    rp=t.RiskPolicy(**risk)
    allocation=dict(params['allocation']); aid=allocation.pop('policy_id'); allocation['registered_at']=datetime.fromisoformat(allocation['registered_at'])
    ap=t.AllocationPolicy(**allocation)
    if rp.policy_id!=rid or ap.policy_id!=aid: raise ValueError('changed policy identity')
    return rp,ap


def _mask_world(world,mask):
    markets=tuple(m if m.symbol in mask.symbols else WorldMarket(m.symbol,None,None,None,None) for m in world.markets)
    def quality(kind,original):
        evidence=[getattr(m,kind) for m in markets if getattr(m,kind) is not None]
        times=[e.exchange_at for e in evidence if e.exchange_at is not None]
        unknown=tuple(e.symbol for e in evidence if e.exchange_at is None)
        missing=tuple(m.symbol for m in markets if getattr(m,kind) is None)
        known=bool(times) and not unknown
        return DataQuality('INCOMPLETE' if missing else 'COMPLETE',original.capture_span_seconds if evidence else None,
            (max(times)-min(times)).total_seconds() if known else None,(world.as_of-min(times)).total_seconds() if known else None,
            max((world.as_of-e.available_at).total_seconds() for e in evidence) if evidence else None,
            missing,unknown,original.source_errors,original.clock_state,world.as_of)
    return replace(world,markets=markets,book_quality=quality('book',world.book_quality),premium_quality=quality('premium',world.premium_quality))


def run_shadow_once(universe_directory,book_directory,radar_config_directory,ranking_policy_directory,mask_directory,config_directory,output_directory,*,premium_directory=None):
    saved=c._read_json(Path(config_directory)/'config.json'); payload=saved['payload']; params=payload['parameters']
    if set(saved)!={'payload','commitment'} or saved['commitment']!=c.commitment(payload) or params!=c._read_json(Path(config_directory)/'parameters.json'):
        raise ValueError('shadow configuration integrity failure')
    if set(payload)!={'parameters','frozen_at'} or set(params)!={'universe_id','radar_id','ranking_id','mask_id','mask_name','risk','allocation','equity','budget','requested_risk','kill_switch','role','thesis_policy','forecast_producer'}:
        raise ValueError('unknown shadow config fields')
    if (params['role'],params['thesis_policy'],params['forecast_producer'])!=('PILOT','REFERENCE_NON_VALIDATED_v0','UNKNOWN_DIRECTION_v0'):
        raise ValueError('unsupported shadow producers')
    frozen=datetime.fromisoformat(payload['frozen_at']); c.utc(frozen)
    rp,ap=_policies(params)
    radar_config=load_radar_config(radar_config_directory,universe_directory); ranking_policy=t.load_ranking_policy(ranking_policy_directory)
    mask=next(m for m in load_masks(mask_directory,universe_directory) if m.name==params['mask_name'])
    if (radar_config.config_id,ranking_policy.policy_id,mask.mask_id)!=(params['radar_id'],params['ranking_id'],params['mask_id']): raise ValueError('configuration dependencies changed')
    if max(radar_config.frozen_at,ranking_policy.registered_at,mask.frozen_at,rp.registered_at,ap.registered_at)>frozen: raise ValueError('configuration predates dependency')
    book=c.load_cycle(book_directory,universe_directory); premium=None if premium_directory is None else load_premium_cycle(premium_directory,universe_directory)
    cutoff=c._now(); c.utc(cutoff)
    if book.universe_id!=params['universe_id'] or any(s.started_at<frozen or s.completed_at>cutoff for s in ((book,) if premium is None else (book,premium))):
        raise ValueError('not prospective to registered shadow configuration')
    inputs=dict(config=saved['commitment'],book=book.cycle_id,premium=None if premium is None else premium.cycle_id)
    key=c.commitment(inputs); root=Path(output_directory)/key
    if root.exists():
        old=c._read_json(root/'decision.json')
        if set(old)!={'inputs','decision','commitment'} or old['inputs']!=inputs or old['commitment']!=c.commitment((inputs,old['decision'])):
            raise ValueError('shadow replay integrity failure')
        data=dict(old['decision']); identity=data.pop('decision_id')
        if identity!=c.commitment(data): raise ValueError('shadow decision identity mismatch')
        return identity
    root.mkdir(parents=True,exist_ok=False)
    world=_mask_world(load_world(universe_directory,as_of=cutoff,book_directory=book_directory,premium_directory=premium_directory),mask)
    radar=scan(world,radar_config,generated_at=c._now(),visible_symbols=mask.symbols)
    at=c._now()
    theses=tuple(t.Thesis(candidate,world,at,at,'REFERENCE descriptive observation; no predictive assertion',candidate.evidence_refs,(),
        ('Source evidence is available',),('No contradiction discovery or validated Alpha model',),('Source/provenance invalidated',),saved['commitment']) for candidate in radar.candidates)
    at=c._now()
    forecasts=tuple(t.Forecast(thesis,t.ForecastKind.DIRECTIONAL_VIEW,t.Direction.UNSPECIFIED,t.CalibrationState.UNKNOWN,
        'REFERENCE_UNKNOWN_DIRECTION',saved['commitment'],thesis.supporting_evidence_refs,at,at) for thesis in theses)
    ranking=t.GlobalOpportunityRanker.rank(world,radar,ranking_policy_directory,theses=theses,forecasts=forecasts,available_at=c._now())
    at=c._now(); portfolio=t.PortfolioState(at,at,_amount(params['equity']),_amount(params['budget']),(),saved['commitment'])
    auths=tuple(t.authorize_risk(candidate,world,portfolio,t.Exposure(candidate.candidate_id,candidate.family,
        tuple(t.ExposureLeg(s,t.Direction.UNSPECIFIED) for s in candidate.markets),_amount(params['requested_risk'])),rp,
        kill_switch=params['kill_switch'],available_at=c._now()) for candidate in radar.candidates)
    plan=t.allocate_capital(ranking,portfolio,auths,_amount(params['budget']),ap,available_at=c._now())
    decision=t.ShadowCapitalDecision(world,radar,theses,forecasts,plan,c._now(),saved['commitment'])
    data=t._plain(decision)
    c._write(root/'decision.json',c._json(dict(inputs=inputs,decision=data,commitment=c.commitment((inputs,data)))))
    return decision.decision_id
