"""Already-activated Metrics runtime. No automatic activation or task management.

Transport is explicit; tests inject it. Heartbeat is operational metadata only.
Expected transport failures become FAILED inside the runner and do not stop future
slots. Unexpected contract, filesystem or clock failures stop the runtime closed.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from math import isfinite
import os
from pathlib import Path
import time

from . import metrics_h1_activation as activation
from . import metrics_h1_runner as runner
from . import metrics_h1_live_adapter as adapter


@contextmanager
def process_lock(path):
    if os.name != 'nt':
        raise OSError('Windows runtime required')
    import msvcrt
    activation._reject_aliases(path)
    with Path(path).open('a+b') as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b'\0'); handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError('Metrics runtime already locked') from exc
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _heartbeat(path, body):
    activation._reject_aliases(path)
    temp = path.with_name('.heartbeat.pending')
    runner._write(temp, body)
    os.replace(temp, path)  # Replace operational metadata only, never evidence.


def _anchor(path, config):
    if not path.exists():
        return None
    activation._reject_aliases(path)
    body = adapter._json(path.read_bytes())
    fields = {'schema','activation_id','status','started_at','updated_at','iterations','last_adapter_status','heartbeat_is_evidence','pid'}
    if type(body) is not dict or set(body) != fields:
        raise ValueError('invalid runtime heartbeat')
    if (body['schema'] != 'metrics-h1-heartbeat-v1' or body['activation_id'] != config['activation_id']
            or body['heartbeat_is_evidence'] is not False or body['status'] not in ('STARTED','RUNNING','STOPPED')
            or type(body['iterations']) is not int or body['iterations'] < 0
            or type(body['pid']) is not int or body['pid'] <= 0
            or body['last_adapter_status'] not in (None,'NOT_DUE','SUCCESS','FAILED','INCOMPLETE','EXISTING_NOOP','BEFORE_TARGET','MISSED_SLOT','NOT_ACTIVE')):
        raise ValueError('invalid runtime heartbeat contract')
    started, updated = map(runner._utc,(body['started_at'],body['updated_at']))
    if updated < started or (body['iterations']==0) != (body['last_adapter_status'] is None):
        raise ValueError('invalid heartbeat chronology')
    if body['status']=='STARTED' and (updated != started or body['iterations'] != 0):
        raise ValueError('invalid initial heartbeat')
    return updated


def run_forever(state, *, repo_root, transport, clock=lambda: datetime.now(timezone.utc),
                sleeper=time.sleep, stop_requested=lambda:False, poll_seconds=5, max_iterations=None):
    config = runner.load_config(state, repo_root=repo_root)
    if type(poll_seconds) not in (int,float) or not isfinite(poll_seconds) or not 0 < poll_seconds <= 5:
        raise ValueError('poll interval must be in (0,5]')
    if max_iterations is not None and (type(max_iterations) is not int or max_iterations < 1):
        raise ValueError('positive iteration limit required')
    if not all(callable(x) for x in (transport,clock,sleeper,stop_requested)):
        raise TypeError('callables required')
    runtime = Path(state)/'runtime'
    activation._reject_aliases(runtime)
    runtime.mkdir(exist_ok=True)
    heartbeat = runtime/'heartbeat.json'
    with process_lock(runtime/'runner.lock'):
        if (runtime/'.heartbeat.pending').exists():
            raise ValueError('interrupted heartbeat publication requires inspection')
        previous = _anchor(heartbeat,config)
        invalid_clock = False

        def sample():
            nonlocal previous, invalid_clock
            try:
                value = runner._utc(clock())
                if invalid_clock or (previous is not None and value < previous):
                    raise ValueError('runtime clock moved backwards')
                previous = value
                return value
            except Exception:
                invalid_clock = True
                raise

        started = sample()
        iterations = 0
        last = None

        def write(status):
            _heartbeat(heartbeat, {'schema':'metrics-h1-heartbeat-v1','activation_id':config['activation_id'],
                                   'status':status,'started_at':started.isoformat(),'updated_at':sample().isoformat(),
                                   'iterations':iterations,'last_adapter_status':last,
                                   'heartbeat_is_evidence':False,'pid':os.getpid()})

        # STARTED must represent exactly the initial clock sample.
        _heartbeat(heartbeat, {'schema':'metrics-h1-heartbeat-v1','activation_id':config['activation_id'],
                               'status':'STARTED','started_at':started.isoformat(),'updated_at':started.isoformat(),
                               'iterations':0,'last_adapter_status':None,'heartbeat_is_evidence':False,'pid':os.getpid()})
        while not stop_requested():
            if runner.load_config(state, repo_root=repo_root) != config:
                raise ValueError('activation changed during runtime')
            result = adapter.run_once(state, repo_root=repo_root, transport=transport, clock=sample)
            last = result['status']
            iterations += 1
            write('RUNNING')
            if max_iterations is not None and iterations >= max_iterations:
                break
            sleeper(poll_seconds)
        write('STOPPED')
        return {'status':'STOPPED','iterations':iterations,'last_adapter_status':last}
