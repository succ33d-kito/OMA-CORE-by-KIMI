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


def attempt(session, ledger, state, boundary):
    identity = uuid.uuid4().hex
    started = now()
    base = dict(attempt_id=identity, expected_event_time=boundary.isoformat(), started_at=started.isoformat())
    exclusive_json(Path(state)/'attempts'/(identity+'-start.json'), dict(base, status='STARTED'))
    try:
        x = capture_price_receipt(session, ledger, expected_event_time=boundary)
        body = dict(base, status='SUCCESS', receipt_id=x['id'])
    except Exception as exc:
        body = dict(base, status='CONFLICT' if 'conflicting observation' in str(exc) else 'FAILED', error=str(exc))
    body['completed_at'] = now().isoformat()
    exclusive_json(Path(state)/'attempts'/(identity+'-result.json'), body)
    return body


def run(ledger, state, delay=5):
    import requests
    with runner_lock(state), requests.Session() as session:
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
            boundary = hour(target)
            # A resumed/suspended host never catches up old slots. Retry window 2 min.
            if current <= target + timedelta(minutes=2):
                result = attempt(session, ledger, state, boundary)
                if result['status'] == 'FAILED':
                    time.sleep(20)
                    if target <= now() <= target + timedelta(minutes=2):
                        attempt(session, ledger, state, boundary)
            else:
                exclusive_json(Path(state)/'attempts'/(uuid.uuid4().hex+'-result.json'),
                    dict(status='MISSED_SLOT', expected_event_time=boundary.isoformat(), completed_at=current.isoformat()))
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
    args = parser.parse_args()
    next_capture_at(now(), args.delay)
    Path(args.state).mkdir(parents=True, exist_ok=True)
    if args.command == 'run':
        try:
            run(args.ledger, args.state, args.delay)
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
        for key in ['capture_running', 'last_valid_event_time', 'last_receipt_at',
                    'current_streak', 'longest_streak', 'gaps', 'conflicts', 'invalid',
                    'bars_to_81', 'regime_input_ready', 'ledger_integrity', 'last_external_anchor']:
            print(f'{key.upper()}: {report[key]}')
    return 0 if report['ledger_integrity'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
