"""H1 collector with exclusive attempts, restart verification and no backfill."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
import os
from pathlib import Path
import time

from . import multi_market_capture as c


def next_target(now):
    c.utc(now)
    return now.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1,seconds=5)


def _sealed(payload): return dict(payload=payload,commitment=c.commitment(payload))


def _unseal(path):
    data=c._read_json(path)
    if set(data)!={'payload','commitment'} or data['commitment']!=c.commitment(data['payload']):
        raise ValueError('corrupted collector state')
    return data['payload']


def initialize(root,universe_directory):
    root=Path(root); universe_directory=Path(universe_directory).resolve()
    u=c.load_universe(universe_directory)
    config=dict(schema='multi-market-h1-v0',universe_id=u.universe_id,universe_path=str(universe_directory),cadence='H1',role='PILOT')
    root.mkdir(parents=True,exist_ok=True)
    if (root/'config.json').exists():
        if _unseal(root/'config.json')!=config: raise ValueError('collector configuration changed')
    else:
        if any(p.name!='runner.lock' for p in root.iterdir()): raise ValueError('unrecognized existing state')
        c._write(root/'config.json',c._json(_sealed(config)))
    (root/'attempts').mkdir(exist_ok=True)
    if (root/'health.json').exists(): _unseal(root/'health.json')
    recover(root,universe_directory)
    return root


def recover(root,universe_directory):
    """Verify prior attempts; incomplete directories are retained, never retried."""
    for path in sorted((Path(root)/'attempts').iterdir()):
        if not path.is_dir(): raise ValueError('unexpected attempt artifact')
        at=datetime.strptime(path.name,'%Y%m%dT%H0000Z').replace(tzinfo=c.timezone.utc)
        attempt=c._read_json(path/'attempt.json')
        if attempt!={'slot':at.isoformat(),'kind':'H1'}: raise ValueError('attempt identity conflict')
        if (path/'capture'/'cycle.json').exists():
            cycle=c.load_cycle(path/'capture',universe_directory)
            if cycle.slot!=at or cycle.kind!='H1': raise ValueError('cycle identity conflict')
        else:
            cycle=None
        if (path/'result.json').exists():
            result=_unseal(path/'result.json')
            if set(result)!={'status','cycle_id'} or result['status'] not in ('COMPLETE','INCOMPLETE','FAILED','MISSED_SLOT'):
                raise ValueError('unexpected result')
            if cycle is not None:
                if result!={'status':cycle.completeness,'cycle_id':cycle.cycle_id}: raise ValueError('result mismatch')
            elif result['cycle_id'] is not None or result['status'] not in ('FAILED','MISSED_SLOT'):
                raise ValueError('result without evidence')
        # A crash before result publication remains an incomplete attempt.


def run_slot(root,universe_directory,slot):
    c.utc(slot)
    if slot!=slot.replace(minute=0,second=0,microsecond=0): raise ValueError('not H1')
    root=Path(root); path=root/'attempts'/slot.strftime('%Y%m%dT%H0000Z')
    if path.exists():
        recover(root,universe_directory)
        return 'DUPLICATE_NOOP'
    now=c._now()
    if now<slot: raise ValueError('future slot')
    path.mkdir()
    c._write(path/'attempt.json',c._json(dict(slot=slot.isoformat(),kind='H1')))
    if now>=slot+timedelta(minutes=2):
        result=dict(status='MISSED_SLOT',cycle_id=None)
    else:
        try:
            cycle=c.capture_cycle(path/'capture',universe_directory,kind='H1',slot=slot)
        except Exception:
            c._write(path/'result.json',c._json(_sealed(dict(status='FAILED',cycle_id=None))))
            raise  # No silent retry on invalid evidence or transport failure.
        result=dict(status=cycle.completeness,cycle_id=cycle.cycle_id)
    c._write(path/'result.json',c._json(_sealed(result)))
    return result['status']


@contextmanager
def runner_lock(root):
    import msvcrt  # Windows runner only; tests exercise platform-neutral state logic.
    root=Path(root); root.mkdir(parents=True,exist_ok=True)
    with (root/'runner.lock').open('a+b') as lock:
        if lock.seek(0,2)==0: lock.write(b'0'); lock.flush()
        lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try: yield
        finally:
            lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


def health(root,target,status):
    payload=dict(pid=os.getpid(),status=status,next_expected_cycle=target.isoformat(),
                 observed_at=c._now().isoformat(),integrity='PASS' if status=='RUNNING' else 'NOT_CONFIRMED')
    temporary=Path(root)/'health.pending'
    if temporary.exists(): temporary.unlink()  # Sole writer lock held; only mutable health staging.
    c._write(temporary,c._json(_sealed(payload)))
    os.replace(temporary,Path(root)/'health.json')


def run(root,universe_directory):
    with runner_lock(root):
        root=initialize(root,universe_directory)
        previous=c._now(); target=next_target(previous)
        health(root,target,'RUNNING')
        while True:
            now=c._now()
            if now<previous: raise ValueError('clock reversed; collector stopped')
            previous=now
            if now<target:
                time.sleep(min(20,(target-now).total_seconds()))
                continue
            try:
                run_slot(root,universe_directory,target.replace(second=0))
                recover(root,universe_directory)
            except Exception:
                health(root,target,'FAILED')
                raise
            target=next_target(c._now())
            health(root,target,'RUNNING')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',required=True)
    parser.add_argument('--universe',required=True)
    args=parser.parse_args()
    run(args.state,args.universe)


if __name__=='__main__': main()
