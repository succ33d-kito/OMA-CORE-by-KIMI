"""Independent UTC runner. Operational files belong outside the repository."""
import argparse
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.scientific.price_continuity import (next_capture_at, hour, status, anchor,
                                             exclusive_json)
from core.market_mechanics.binance_live_adapter import capture_price_receipt
from core.scientific.prospective_receipts import load_observations, _utc
from core.scientific.capture_clock import ClockHealthError


def now():
    return datetime.now(timezone.utc)


@contextmanager
def runner_lock(state):
    state = Path(state)
    state.mkdir(parents=True, exist_ok=True)
    f = (state/'runner.lock').open('a+b')
    if f.tell() == 0:
        f.write(b'0'); f.flush()
    f.seek(0)
    locked = False
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        yield
    finally:
        if locked:
            f.seek(0)
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()


def running(state):
    try:
        with runner_lock(state):
            return False
    except OSError:
        return True


def atomic_json(path, body):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    exclusive_json(tmp, body)
    os.replace(tmp, path)


def refresh(ledger, state, delay=5):
    report = status(ledger, state, now(), delay)
    report['capture_running'] = running(state)
    heartbeat = Path(state)/'heartbeat.json'
    report['runner'] = json.loads(heartbeat.read_text()) if heartbeat.exists() else None
    report.update(capture_health(report, state))
    atomic_json(Path(state)/'status.json', report)
    if report['certificate']:
        cert = report['certificate']
        path = Path(state)/'certificates'/(cert['certified_set_hash']+'.json')
        if not path.exists():
            try:
                exclusive_json(path, cert)
            except FileExistsError:
                pass  # Another status reader published the same immutable window.
    return report


def capture_health(report, state):
    results = [json.loads(p.read_text()) for p in (Path(state)/'attempts').glob('*-result.json')]
    results.sort(key=lambda x: (x['completed_at'], x.get('attempt_id', '')))
    failures = 0
    for result in reversed(results):
        if result['status'] == 'SUCCESS':
            break
        if result["status"] in ("FAILED", "CONFLICT"):
            failures += 1
    reference = _utc(report['reference_at'])
    receipt = report.get('last_receipt_at')
    age = (reference-_utc(receipt)).total_seconds() if receipt else None
    runner = report.get('runner') or {}
    heartbeat_age = (reference-_utc(runner['at'])).total_seconds() if runner.get('at') else None
    healthy = (report['capture_running'] and report['ledger_integrity'] == 'PASS'
               and heartbeat_age is not None and 0 <= heartbeat_age <= 60
               and age is not None and 0 <= age <= 3600+125 and not failures
               and runner.get('state') != 'CLOCK_REGRESSION')
    health = 'HEALTHY' if healthy else 'DEGRADED'
    if (not report['capture_running'] or report['ledger_integrity'] != 'PASS'
            or heartbeat_age is None or not 0 <= heartbeat_age <= 60
            or runner.get('state') == 'CLOCK_REGRESSION'
            or (results and results[-1].get('failure_kind') == 'CLOCK')):
        health = 'UNHEALTHY'
    return dict(capture_health=health, capture_healthy=healthy,
                last_success_at=next((x['completed_at'] for x in reversed(results)
                                      if x['status'] == 'SUCCESS'), None),
                receipt_age_seconds=age, heartbeat_age_seconds=heartbeat_age,
                consecutive_failures=failures,
                missed_slots=sum(x.get('missed_slots', 1) for x in results if x['status'] == 'MISSED_SLOT'),
                clock_failures=sum(x['status'] == 'FAILED' and x.get('failure_kind') == 'CLOCK' for x in results))


def attempt(session, ledger, state, boundary, deadline=None):
    identity = uuid.uuid4().hex
    started = now()
    base = dict(attempt_id=identity, expected_event_time=boundary.isoformat(), started_at=started.isoformat())
    exclusive_json(Path(state)/'attempts'/(identity+'-start.json'), dict(base, status='STARTED'))
    try:
        options = dict(expected_event_time=boundary)
        if deadline is not None:
            options.update(capture_deadline=deadline, timeout=min(10, max(.1, (deadline-started).total_seconds()/2)))
        x = capture_price_receipt(session, ledger, **options)
        body = dict(base, status='SUCCESS', receipt_id=x['id'])
    except Exception as exc:
        body = dict(base, status='CONFLICT' if 'conflicting observation' in str(exc) else 'FAILED', error=str(exc))
        body['failure_kind'] = 'CLOCK' if isinstance(exc, ClockHealthError) or 'clock' in str(exc) else 'CAPTURE'
    body['completed_at'] = now().isoformat()
    exclusive_json(Path(state)/'attempts'/(identity+'-result.json'), body)
    return body


def capture_slot(session, ledger, state, target):
    deadline = target + timedelta(minutes=2)
    current = now()
    if current > deadline:
        exclusive_json(Path(state)/'attempts'/(uuid.uuid4().hex+'-result.json'),
            dict(status='MISSED_SLOT', expected_event_time=hour(target).isoformat(),
                 completed_at=current.isoformat(), missed_slots=1+int((hour(current)-hour(target)).total_seconds()/3600)))
        return
    previous = current
    result = None
    def exhausted(result):
        exclusive_json(Path(state)/'attempts'/(uuid.uuid4().hex+'-result.json'),
            dict(status='MISSED_SLOT', expected_event_time=hour(target).isoformat(),
                 completed_at=now().isoformat(), missed_slots=1,
                 failure_kind=result.get('failure_kind'), error=result.get('error')))
        return result
    while target <= current < deadline:
        result = attempt(session, ledger, state, hour(target), deadline)
        if result['status'] != 'FAILED':
            return result
        current = now()
        if current < previous:
            raise ClockHealthError('clock moved backwards during retries')
        remaining = (deadline-current).total_seconds()
        if remaining <= 0:
            return exhausted(result)
        time.sleep(min(20, remaining))
        previous, current = current, now()
        if current < previous:
            raise ClockHealthError('clock moved backwards during retry wait')
    return exhausted(result) if result else None


@contextmanager
def prevent_sleep(enabled=False):
    """Optional thread-scoped Windows request; release even on exceptions."""
    if not enabled or os.name != 'nt':
        yield
        return
    import ctypes
    set_state = ctypes.windll.kernel32.SetThreadExecutionState
    if not set_state(0x80000001):
        raise OSError('Windows sleep protection request failed')
    try:
        yield
    finally:
        if not set_state(0x80000000):
            raise OSError('Windows sleep protection release failed')


def run(ledger, state, delay=5, keep_awake=False):
    import requests
    with runner_lock(state), requests.Session() as session, prevent_sleep(keep_awake):
        report = refresh(ledger, state, delay)
        if report['ledger_integrity'] != 'PASS':
            raise ValueError(report.get('integrity_error', 'ledger integrity failure'))
        anchor(ledger, state, now())
        previous = now()
        if any(_utc(x['recorded_at']) > previous for x in load_observations(ledger).values()):
            raise ValueError('clock regression relative to persisted ledger')
        heartbeat_path = Path(state)/'heartbeat.json'
        if heartbeat_path.exists() and _utc(json.loads(heartbeat_path.read_text())['at']) > previous:
            raise ValueError('clock regression relative to previous process')
        slot = hour(previous) + timedelta(seconds=delay)
        target = slot if slot <= previous <= slot+timedelta(minutes=2) else next_capture_at(previous, delay)
        while True:
            current = now()
            if current < previous:
                atomic_json(Path(state)/'heartbeat.json', dict(state='CLOCK_REGRESSION', at=previous.isoformat(), observed_at=current.isoformat()))
                raise ValueError('clock moved backwards; restart only after host clock is corrected')
            previous = current
            atomic_json(Path(state)/'heartbeat.json', dict(state='WAITING', at=current.isoformat(), next_capture_at=target.isoformat(), pid=os.getpid()))
            if current < target:
                time.sleep(min(20, (target-current).total_seconds()))
                continue
            # A resumed/suspended host never catches up old slots. Retry window 2 min.
            capture_slot(session, ledger, state, target)
            completed = now()
            if completed < current or any(_utc(x['recorded_at']) > completed for x in load_observations(ledger).values()):
                raise ValueError('clock regression during capture')
            previous = completed
            report = refresh(ledger, state, delay)
            if report['ledger_integrity'] != 'PASS':
                raise ValueError(report.get('integrity_error'))
            anchor(ledger, state, now())
            refresh(ledger, state, delay)
            target = next_capture_at(now(), delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'status', 'anchor'])
    parser.add_argument('--ledger', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--delay', type=int, default=5)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--keep-awake', action='store_true', help='Request thread-scoped Windows sleep protection while running')
    args = parser.parse_args()
    next_capture_at(now(), args.delay)
    Path(args.state).mkdir(parents=True, exist_ok=True)
    if args.command == 'run':
        try:
            run(args.ledger, args.state, args.delay, args.keep_awake)
        except Exception as exc:
            exclusive_json(Path(args.state)/'errors'/(uuid.uuid4().hex+'.json'),
                           dict(at=now().isoformat(), error=str(exc)))
            raise
        return 0
    if args.command == 'anchor':
        anchor(args.ledger, args.state, now())
    report = refresh(args.ledger, args.state, args.delay)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for key in ['capture_running', 'capture_health', 'last_success_at', 'receipt_age_seconds',
                    'consecutive_failures', 'missed_slots', 'clock_failures', 'last_valid_event_time', 'last_receipt_at',
                    'current_streak', 'longest_streak', 'gaps', 'conflicts', 'invalid',
                    'bars_to_81', 'regime_input_ready', 'ledger_integrity', 'last_external_anchor']:
            print(f'{key.upper()}: {report[key]}')
    return 0 if report['ledger_integrity'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
