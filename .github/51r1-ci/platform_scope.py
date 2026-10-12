"""Explicit hybrid scope: unchanged Windows contracts, independently tested on Windows.
No source monkeypatches, outcome-based selection, or blanket module exclusions.
"""
from pathlib import Path
import json
import sys
import pytest

SCOPE = json.loads(Path(__file__).with_name("windows-scope.json").read_text())

def pytest_collection_modifyitems(items):
    if sys.platform != "linux":
        raise pytest.UsageError("This CI partition is qualified only for Linux")
    found = {item.nodeid for item in items}
    if set(SCOPE) - found:
        raise pytest.UsageError("Windows validation manifest references missing tests")
    for item in items:
        if item.nodeid in SCOPE:
            record = SCOPE[item.nodeid]
            reason = "WINDOWS_CONTRACT: independently verified " + record["result"]
            if record["skip_reason"]:
                reason += "; " + record["skip_reason"]
            item.add_marker(pytest.mark.skip(reason=reason))
