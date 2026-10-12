"""Locked runtime for existing PILOT activation. Never initializes scientific state."""
from datetime import timedelta
import json
import os
import time
from . import price_role_h1_runner as runner
from .funding_h1_runtime import _process_lock, _atomic_json
from .metrics_h1_activation import _reject_aliases

SCHEMA = "price-role-h1-runtime-v1"


def run_forever(state, *, repo_root, session=None, clock=runner.now, sleeper=time.sleep,
                stop_requested=lambda:False, max_iterations=None, run_slot=runner.attempt_slot):
    root, config = runner.validate_state(state, repo_root=repo_root)
    if max_iterations is not None and (type(max_iterations) is not int or max_iterations < 1):
        raise ValueError("positive iteration bound required")
    runtime = root / "runtime"
    runtime.mkdir(exist_ok=True)
    heartbeat, lock = runtime/"heartbeat.json", runtime/"runner.lock"
    for path in (heartbeat, lock, runtime/".heartbeat.json.tmp"):
        _reject_aliases(path)
    with _process_lock(lock):
        prior = runner.utc(config["not_before"])
        if heartbeat.exists():
            body = json.loads(heartbeat.read_text())
            if body.get("schema") != SCHEMA or body.get("activation_id") != config["activation_id"] or body.get("heartbeat_is_evidence") is not False:
                raise ValueError("invalid operational heartbeat")
            prior = max(prior, runner.utc(body["updated_at"]))
        def sample():
            nonlocal prior
            value = runner.utc(clock())
            if value < prior:
                raise ValueError("Price runtime clock moved backwards")
            prior = value
            return value
        started = sample()
        last = None
        def write(status):
            _reject_aliases(heartbeat)
            _reject_aliases(runtime/".heartbeat.json.tmp")
            _atomic_json(heartbeat, {"schema":SCHEMA,"activation_id":config["activation_id"],
                "status":status,"started_at":started.isoformat(),"updated_at":sample().isoformat(),
                "pid":os.getpid(),"heartbeat_is_evidence":False,
                "last_slot":None if last is None else last["slot"],
                "last_result":None if last is None else last["status"]})
        write("STARTED")
        # Recovery visits only already-persisted raw observations, never historical capture slots.
        known = runner._rows(root)
        for slot in sorted({runner.utc(r["event_time"]) for r in known.values() if r["feature"] == "Price/OHLCV"}):
            def no_network(*args, **kwargs):
                raise RuntimeError("network forbidden during raw-only recovery")
            # A recovery call cannot acquire a new authorization for existing raw.
            last = runner.attempt_slot(root,slot,repo_root=repo_root,clock=sample,capture=no_network)
        current = sample()
        target_slot = current.replace(minute=0,second=0,microsecond=0)
        if current > runner.bounds(target_slot)[1]:
            target_slot += timedelta(hours=1)
        iterations = 0
        try:
            while not stop_requested():
                current = sample()
                if current >= runner.bounds(target_slot)[0]:
                    last = run_slot(root,target_slot,repo_root=repo_root,session=session,clock=sample)
                    completed = sample()
                    # Terminal result or attestation failure: next future slot, never recapture.
                    target_slot = max(target_slot+timedelta(hours=1),
                        completed.replace(minute=0,second=0,microsecond=0))
                    if completed > runner.bounds(target_slot)[1]:
                        target_slot += timedelta(hours=1)
                write("RUNNING")
                iterations += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break
                sleeper(5)
        except Exception:
            write("FAILED")
            raise
        write("STOPPED")
        return {"schema":SCHEMA,"status":"STOPPED","iterations":iterations,"last_result":last}
