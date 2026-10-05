"""Append-only coverage records and outcome-independent frozen visibility masks."""
from dataclasses import dataclass,asdict
from datetime import datetime
from pathlib import Path
from . import multi_market_capture as c
from .world_state import _normalize
from .opportunity_radar import RadarResult


@dataclass(frozen=True,slots=True)
class VisibilityMask:
    name: str
    universe_id: str
    frozen_at: datetime
    symbols: tuple[str,...]
    requested_size: int
    mask_id: str


def _masks(u,at):
    c.utc(at)
    if at<u.frozen_at: raise ValueError('mask predates universe')
    result=[]
    for name,count in (('Retail-1',1),('Retail-5',5),('Retail-20',20),('OMA-FULL',len(u.symbols))):
        symbols=u.symbols[:count]
        identity=c.commitment((name,u.universe_id,at.isoformat(),symbols,count,'LEXICOGRAPHIC-v0'))
        result.append(VisibilityMask(name,u.universe_id,at,symbols,count,identity))
    return tuple(result)


def freeze_masks(directory,universe_directory):
    u=c.load_universe(universe_directory); at=c._now()
    masks=_masks(u,at); root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    payload=_normalize([asdict(m) for m in masks])
    c._write(root/'masks.json',c._json(dict(payload=payload,commitment=c.commitment(payload))))
    return load_masks(root,universe_directory)


def load_masks(directory,universe_directory):
    u=c.load_universe(universe_directory); saved=c._read_json(Path(directory)/'masks.json')
    if set(saved)!={'payload','commitment'} or c.commitment(saved['payload'])!=saved['commitment']:
        raise ValueError('mask commitment mismatch')
    at=datetime.fromisoformat(saved['payload'][0]['frozen_at'])
    masks=_masks(u,at)
    if saved['payload']!=_normalize([asdict(m) for m in masks]): raise ValueError('mask definitions changed')
    return masks


def _payload(radar):
    if type(radar) is not RadarResult or radar.role!='PILOT': raise TypeError('PILOT RadarResult required')
    universe=radar.universe
    subjects=tuple(s for s,_ in radar.candidate_subjects)
    others=tuple(s for s,_ in radar.non_candidates)
    if len(set(universe))!=len(universe) or len(subjects+others)!=len(universe) or set(subjects)&set(others) or set(subjects+others)!=set(universe):
        raise ValueError('invalid candidate population accounting')
    if set(radar.observed)&set(radar.missing) or set(radar.observed+radar.missing)!=set(universe):
        raise ValueError('invalid observed/missing accounting')
    if tuple(cid for _,cid in radar.candidate_subjects)!=tuple(x.candidate_id for x in radar.candidates):
        raise ValueError('candidate identity mismatch')
    if any(x.world_state_id!=radar.world_state_id or x.role!=radar.role for x in radar.candidates):
        raise ValueError('candidate scope conflict')
    return _normalize(dict(universe_size=len(universe),universe=universe,observed_count=len(radar.observed),
        observed=radar.observed,candidate_count=len(radar.candidates),candidate_identities=tuple(x.candidate_id for x in radar.candidates),
        candidate_subjects=radar.candidate_subjects,non_candidates=radar.non_candidates,missing_markets=radar.missing,
        world_state_id=radar.world_state_id,radar_id=radar.radar_id,radar_version=radar.version,config_id=radar.config_id,
        universe_id=radar.universe_id,timestamp=radar.generated_at,role=radar.role,visible_symbols=radar.visible_symbols,
        visibility='OMA-FULL' if radar.visible_symbols==radar.universe else 'MASKED_PROJECTION'))


def load_entry(path):
    path=Path(path); saved=c._read_json(path)
    if set(saved)!={'payload','recorded_at','commitment'}: raise ValueError('unknown ledger fields')
    if saved['commitment']!=c.commitment((saved['payload'],saved['recorded_at'])) or path.stem!=c.commitment(saved['payload']):
        raise ValueError('coverage integrity failure')
    recorded=datetime.fromisoformat(saved['recorded_at']); generated=datetime.fromisoformat(saved['payload']['timestamp'])
    c.utc(recorded); c.utc(generated)
    if recorded<generated: raise ValueError('coverage precedes radar')
    return saved


def append_coverage(directory,radar):
    payload=_payload(radar); eid=c.commitment(payload)
    root=Path(directory); root.mkdir(parents=True,exist_ok=True); path=root/(eid+'.json')
    if path.exists():
        if load_entry(path)['payload']!=payload: raise ValueError('coverage conflict')
        return eid
    at=c._now(); c.utc(at)
    if at<radar.generated_at: raise ValueError('future radar')
    record=dict(payload=payload,recorded_at=at.isoformat(),commitment=c.commitment((payload,at.isoformat())))
    c._write(path,c._json(record))
    load_entry(path)
    return eid
