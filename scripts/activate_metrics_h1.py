"""Exact-plan operator activation; no HTTP, runtime or scheduler side effects."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from core.scientific import metrics_h1_activation as activation

MAX_AGE = timedelta(seconds=60)


def _now():
    return datetime.now(timezone.utc)


def _repository():
    root = REPO_ROOT.resolve(strict=True)
    def git(*args):
        return subprocess.check_output(['git','-c','safe.directory='+str(root),'-C',str(root),*args],
                                       text=True,stderr=subprocess.PIPE).strip()
    if Path(git('rev-parse','--show-toplevel')).resolve(strict=True) != root:
        raise ValueError('repository root mismatch')
    return {'head':git('rev-parse','HEAD'), 'branch':git('branch','--show-current'),
            'dirty':bool(git('status','--porcelain','--untracked-files=all')),
            'root':str(root),
            'activation_sha256':hashlib.sha256(Path(activation.__file__).read_bytes()).hexdigest(),
            'ceremony_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _prepare(state, role, now):
    now = activation._utc(now)
    design = activation._design()
    root = activation.validate_state_root(state, repo_root=REPO_ROOT)
    # Reuse the authority's strict role check and slot selection.
    config = activation._config(root, now, role, design)
    return {'schema':'metrics-h1-operator-plan-v1', 'repository':_repository(),
            'state_root':str(root), 'dataset_role':config['dataset_role'],
            'observed_at':now.isoformat(), 'activation_slot':config['activation_slot'],
            'frozen_sha256':dict(activation._FROZEN), 'capture':design['capture'],
            'state_exists':root.exists(),
            'activation_residue':sorted(p.name for p in root.parent.glob('.'+root.name+'.activating-*')),
            'starts_runtime':False, 'installs_task':False, 'network_executed':False}


def prepare(state, role):
    return _prepare(state, role, _now())


def confirmation(plan):
    return 'ACTIVATE-METRICS-H1:'+hashlib.sha256(activation._canonical(plan)).hexdigest()


def execute(plan, token):
    if type(plan) is not dict or token != confirmation(plan):
        raise ValueError('exact-plan confirmation required')
    observed = activation._utc(datetime.fromisoformat(plan['observed_at']))
    current = activation._utc(_now())
    if not timedelta(0) <= current-observed <= MAX_AGE:
        raise ValueError('expired plan or clock regression')
    expected = _prepare(plan['state_root'], plan['dataset_role'], observed)
    if activation._canonical(plan) != activation._canonical(expected):
        raise ValueError('plan changed; prepare again')
    if expected['repository']['dirty']:
        raise ValueError('clean repository required')
    if expected['state_exists'] or expected['activation_residue']:
        raise FileExistsError('state or staging residue exists')
    final = activation._utc(_now())
    if final < current or final-observed > MAX_AGE:
        raise ValueError('expired plan or clock regression')
    if activation.select_activation_slot(final).isoformat() != plan['activation_slot']:
        raise ValueError('activation boundary changed; prepare again')
    return activation.activate(plan['state_root'],repo_root=REPO_ROOT,now=final,
                               dataset_role=plan['dataset_role'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    plan = commands.add_parser('plan')
    plan.add_argument('--state',required=True)
    plan.add_argument('--role',required=True,choices=('PILOT','DISCOVERY','CONFIRMATION'))
    commit = commands.add_parser('activate')
    commit.add_argument('--plan',required=True)
    commit.add_argument('--confirm',required=True)
    args = parser.parse_args(argv)
    if args.command=='plan':
        body = prepare(args.state,args.role)
        result = {'plan':body,'confirmation':confirmation(body)}
    else:
        # Reject ambiguous duplicate keys and non-finite JSON without loading HTTP.
        from core.scientific.metrics_h1_live_adapter import _json
        envelope = _json(Path(args.plan).read_bytes())
        if type(envelope) is not dict or set(envelope) != {'plan','confirmation'}:
            raise ValueError('plan envelope required')
        if envelope['confirmation'] != args.confirm:
            raise ValueError('confirmation mismatch')
        result = execute(envelope['plan'],args.confirm)
    print(activation._canonical(result).decode())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
