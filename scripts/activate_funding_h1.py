"""Explicit operator ceremony; no scheduler, runtime, capture or network calls."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from core.scientific import funding_h1_activation as activation

SCHEMA = "funding-h1-operator-plan-v1"
MAX_PLAN_AGE = timedelta(seconds=60)
DESIGN_BLOB = '23e1f78504448a4fd8a921110e5d7f6a31e88caa'
DESIGN_SHA256 = 'b07a56978b557bbf49bf155834bdb0784b4a382ff0e481dcced3f776e9b0afab'


def _now():
    return datetime.now(timezone.utc)


def _design():
    raw = (REPO_ROOT / 'docs/FUNDING_H1_RUNTIME_DESIGN.json').read_bytes()
    value = json.loads(raw)
    blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    digest = hashlib.sha256(canonical(value).encode()).hexdigest()
    if blob != DESIGN_BLOB or digest != DESIGN_SHA256:
        raise ValueError('frozen design identity changed')
    if value['schema'] != 'funding-h1-runtime-design-v2' or value['activation'] != {
        'adapter_may_initialize':False,'authority':'EXPLICIT_OPERATOR_TRANSACTION',
        'immutable_after_initialize':True,'minimum_lead_seconds':600,
        'runtime_may_initialize':False,'task_installer_may_initialize':False,
        'selection_rule':'FIRST_UTC_HOUR_BOUNDARY_AT_OR_AFTER_NOW_PLUS_600_SECONDS'}:
        raise ValueError('design activation semantics mismatch')
    if value['capture'] != {'backfill':False,'cadence':'H1','deadline_offset_seconds':120,
        'historical_repair':False,'interpolation':False,'same_slot_retry':'NONE',
        'synthetic_availability':False,'target_offset_seconds':15}:
        raise ValueError('design capture semantics mismatch')
    if value['state_root_policy'] != {'authority':'EXPLICIT_OPERATOR_TRANSACTION',
        'must_be_outside_repository':True,'required_leaf':'funding-h1-v1',
        'resolved_only_during_explicit_activation':True,
        'template':r'%USERPROFILE%\Documents\O-C data\prospective\funding-h1-v1'}:
        raise ValueError('design state policy mismatch')
    return {'sha256':digest,'git_blob':blob}


def _repository():
    root = REPO_ROOT.resolve(strict=True)
    def git(*args):
        return subprocess.check_output(['git','-c','safe.directory='+str(root),'-C',str(root),*args],
            text=True,stderr=subprocess.PIPE).strip()
    if Path(git('rev-parse','--show-toplevel')).resolve(strict=True) != root:
        raise ValueError('repository root mismatch')
    return {'root':str(root),'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),
        'dirty':bool(git('status','--porcelain','--untracked-files=all')),
        'activation_sha256':hashlib.sha256((root/'core/scientific/funding_h1_activation.py').read_bytes()).hexdigest(),
        'ceremony_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def _reject_reparse(path):
    for component in (path,*path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('state path reparse/symlink ambiguity')


def _root():
    profile = Path(os.environ['USERPROFILE'])
    if not profile.is_absolute(): raise ValueError('absolute USERPROFILE required')
    path = profile/'Documents'/'O-C data'/'prospective'/'funding-h1-v1'
    _reject_reparse(path)
    return activation.validate_state_root(path,repo_root=REPO_ROOT)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def confirmation(plan):
    return "ACTIVATE-FUNDING-H1:" + hashlib.sha256(canonical(plan).encode()).hexdigest()


def _prepare_at(now):
    now = activation._utc(now)
    design = _design()
    repo = _repository()
    root = _root()
    return {
        "schema": SCHEMA,
        "repository": repo,
        "design": design,
        "state_root": str(root),
        "observed_at": now.isoformat(),
        "activation_slot": activation.select_activation_slot(now).isoformat(),
        "minimum_lead_seconds": 600,
        "target_offset_seconds": 15,
        "slot_deadline_seconds": 120,
        "retry_policy": "NONE",
        "backfill": False,
        "state_exists": root.exists(),
        "activation_residue": [p.name for p in activation._activation_residue(root)],
        "creates_state_only": True,
        "installs_task": False,
        "starts_runtime": False,
    }


def prepare():
    """Read-only plan; neither paths nor authoritative time are caller inputs."""
    return _prepare_at(_now())


def execute(plan, token):
    if not isinstance(plan, dict):
        raise ValueError("operator plan must be object")
    if token != confirmation(plan):
        raise ValueError("explicit exact-plan confirmation required")
    observed = activation._utc(plan["observed_at"])
    current = activation._utc(_now())
    if not timedelta(0) <= current - observed <= MAX_PLAN_AGE:
        raise ValueError("operator plan expired or clock regressed; prepare again")
    expected = _prepare_at(observed)
    if plan != expected:
        raise ValueError("operator plan contract mismatch")
    if expected['state_exists'] or expected['activation_residue']:
        raise FileExistsError('state or staging residue exists')
    if expected['repository']['dirty']:
        raise ValueError('clean repository required for activation')
    # Resample after potentially slow read-only identity/path checks.
    current = activation._utc(_now())
    if not timedelta(0) <= current-observed <= MAX_PLAN_AGE:
        raise ValueError('operator plan expired or clock regressed; prepare again')
    if activation.select_activation_slot(current).isoformat() != plan["activation_slot"]:
        raise ValueError("activation boundary changed; prepare again")
    if activation._utc(plan['activation_slot']) < current + activation.MINIMUM_LEAD:
        raise ValueError('minimum lead no longer holds')
    return activation.activate(plan["state_root"], now=current, repo_root=REPO_ROOT)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    commit = commands.add_parser("activate")
    commit.add_argument("--plan", required=True)
    commit.add_argument("--confirm", required=True)
    args = parser.parse_args(argv)
    if args.command == "plan":
        plan = prepare()
        result = {"plan": plan, "confirmation": confirmation(plan)}
    else:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
        result = execute(plan, args.confirm)
    print(canonical(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
