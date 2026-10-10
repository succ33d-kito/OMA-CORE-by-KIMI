"""Explicit Metrics execution boundary. Never activates state or installs tasks."""
import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.scientific import metrics_h1_runner as runner
from core.scientific import metrics_h1_runtime as runtime


def check_state(value):
    config = runner.load_config(value, repo_root=REPO_ROOT)
    return {
        'schema': 'metrics-h1-execution-wrapper-v1',
        'status': 'CONFIG_VERIFIED',
        'state': config['state_root'],
        'activation_id': config['activation_id'],
        'activation_slot': config['activation_slot'],
        'dataset_role': config['dataset_role'],
        'network_executed': False,
        'state_initialized': False,
        'runtime_liveness': 'UNVERIFIED',
    }


def main(argv=None, *, run_runtime=None, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check').add_argument('--state', required=True)
    run = commands.add_parser('run')
    run.add_argument('--state', required=True)
    run.add_argument('--allow-public-http', action='store_true', required=True)
    args = parser.parse_args(argv)
    checked = check_state(args.state)
    if args.command == 'check':
        print(json.dumps(checked, sort_keys=True, allow_nan=False))
        return 0
    if run_runtime is None:
        run_runtime = runtime.run_forever
    if transport is None:
        # Importing/checking this wrapper never loads the networking dependency.
        from core.scientific.metrics_h1_http_transport import public_http_transport
        transport = public_http_transport
    if not callable(run_runtime) or not callable(transport):
        raise TypeError('runtime and transport must be callable')
    run_runtime(Path(checked['state']), repo_root=REPO_ROOT, transport=transport)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
