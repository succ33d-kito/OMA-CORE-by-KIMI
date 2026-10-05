"""One verified source pair -> persisted WorldState/Radar/Coverage. No deployment."""
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from . import multi_market_capture as c
from .multi_market_premium import load_premium_cycle
from .world_state import load_world,_normalize
from .opportunity_radar import RadarConfig,scan
from .coverage_ledger import append_coverage,load_entry


def freeze_config(directory,universe_directory,*,mark_index_fraction,funding_fraction_difference,
                  relative_spread_difference,max_candidates,horizon_seconds):
    u=c.load_universe(universe_directory)
    root=Path(directory); root.mkdir(parents=True,exist_ok=False)
    parameters=_normalize(dict(universe_id=u.universe_id,mark_index_fraction=mark_index_fraction,
        funding_fraction_difference=funding_fraction_difference,relative_spread_difference=relative_spread_difference,
        max_candidates=max_candidates,horizon_seconds=horizon_seconds))
    c._write(root/'parameters.json',c._json(parameters))
    config=RadarConfig(c._now(),mark_index_fraction,funding_fraction_difference,relative_spread_difference,max_candidates,horizon_seconds)
    if config.frozen_at<u.frozen_at: raise ValueError('configuration before universe')
    payload=dict(universe_id=u.universe_id,parameters_commitment=c.commitment(parameters),config=_normalize(asdict(config)))
    c._write(root/'config.json',c._json(dict(payload=payload,commitment=c.commitment(payload))))
    return config


def load_config(directory,universe_directory):
    u=c.load_universe(universe_directory); saved=c._read_json(Path(directory)/'config.json')
    if set(saved)!={'payload','commitment'} or saved['commitment']!=c.commitment(saved['payload']): raise ValueError('invalid config commitment')
    p=saved['payload']
    if set(p)!={'universe_id','parameters_commitment','config'} or p['universe_id']!=u.universe_id: raise ValueError('wrong config universe')
    parameters=c._read_json(Path(directory)/'parameters.json')
    if c.commitment(parameters)!=p['parameters_commitment']: raise ValueError('configuration parameters changed')
    values=dict(p['config']); identity=values.pop('config_id')
    values['frozen_at']=datetime.fromisoformat(values['frozen_at'])
    for key in ('mark_index_fraction','funding_fraction_difference','relative_spread_difference'): values[key]=Decimal(values[key])
    config=RadarConfig(**values)
    expected=_normalize(dict(universe_id=u.universe_id,**{k:getattr(config,k) for k in
        ('mark_index_fraction','funding_fraction_difference','relative_spread_difference','max_candidates','horizon_seconds')}))
    if parameters!=expected: raise ValueError('configuration parameter mismatch')
    if config.config_id!=identity or config.frozen_at<u.frozen_at: raise ValueError('invalid config identity/time')
    return config


def run_once(universe_directory,book_directory,config_directory,ledger_directory,*,premium_directory=None):
    config=load_config(config_directory,universe_directory)
    book=c.load_cycle(book_directory,universe_directory)
    premium=None if premium_directory is None else load_premium_cycle(premium_directory,universe_directory)
    cutoff=c._now(); c.utc(cutoff)
    sources=(book,) if premium is None else (book,premium)
    if any(s.completed_at>cutoff or s.started_at<config.frozen_at for s in sources):
        raise ValueError('source is future or predates ex-ante config')
    inputs=dict(universe_id=book.universe_id,book_cycle_id=book.cycle_id,
                premium_cycle_id=None if premium is None else premium.cycle_id,config_id=config.config_id)
    key=c.commitment(inputs); root=Path(ledger_directory)
    entries=root/'entries'; runs=root/'runs'
    entries.mkdir(parents=True,exist_ok=True); runs.mkdir(exist_ok=True)
    for p in entries.iterdir():
        if not p.is_file() or p.suffix!='.json': raise ValueError('unexpected coverage artifact')
        load_entry(p)
    run=runs/key
    if run.exists():
        if c._read_json(run/'inputs.json')!=inputs: raise ValueError('run input conflict')
        saved=c._read_json(run/'result.json')  # Incomplete runs fail closed, no reconstruction.
        if set(saved)!={'inputs','entry_id','world_commitment','radar_commitment'} or saved['inputs']!=inputs:
            raise ValueError('run conflict')
        for artifact in ('world','radar'):
            if c.commitment(c._read_json(run/(artifact+'.json')))!=saved[artifact+'_commitment']: raise ValueError('run artifact mismatch')
        entry=load_entry(entries/(saved['entry_id']+'.json'))
        if entry['payload']['world_state_id']!=c._read_json(run/'world.json')['world_state_id'] or entry['payload']['radar_id']!=c._read_json(run/'radar.json')['radar_id']:
            raise ValueError('run/ledger linkage mismatch')
        return saved['entry_id']
    run.mkdir()
    c._write(run/'inputs.json',c._json(inputs))
    world=load_world(universe_directory,as_of=cutoff,book_directory=book_directory,premium_directory=premium_directory)
    radar=scan(world,config,generated_at=c._now())
    world_data=_normalize(asdict(world)); radar_data=_normalize(asdict(radar))
    c._write(run/'world.json',c._json(world_data)); c._write(run/'radar.json',c._json(radar_data))
    eid=append_coverage(entries,radar)
    c._write(run/'result.json',c._json(dict(inputs=inputs,entry_id=eid,
        world_commitment=c.commitment(world_data),radar_commitment=c.commitment(radar_data))))
    return eid
