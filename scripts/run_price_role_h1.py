"""Explicit Price role runtime boundary: check/status never capture or activate."""
import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))
from core.scientific import price_role_h1_runner as runner
from core.scientific import price_role_h1_runtime as runtime


def main(argv=None, *, run_runtime=None, session_factory=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command",required=True)
    for name in ("check","status","run"):
        command = commands.add_parser(name)
        command.add_argument("--state",required=True)
        if name == "run":
            command.add_argument("--allow-public-http",action="store_true",required=True)
    args = parser.parse_args(argv)
    root, config = runner.validate_state(args.state,repo_root=REPO_ROOT)
    if args.command == "check":
        print(json.dumps({"schema":"price-role-h1-wrapper-v1","status":"CONFIG_VERIFIED",
            "state":str(root),"dataset_role":config["dataset_role"],"activation_id":config["activation_id"],
            "network_executed":False,"state_initialized":False},sort_keys=True))
    elif args.command == "status":
        print(json.dumps(runner.status(root,repo_root=REPO_ROOT),sort_keys=True))
    else:
        if session_factory is None:
            import requests
            session_factory = requests.Session
        with session_factory() as session:
            (run_runtime or runtime.run_forever)(root,repo_root=REPO_ROOT,session=session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
