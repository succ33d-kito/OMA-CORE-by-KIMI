from pathlib import Path
import os
import sys
import pytest
from scripts.install_prospective_timer import render,install,CALENDAR

def test_user_timer_is_utc_and_no_backfill(tmp_path):
    repo=Path(__file__).resolve().parents[1]
    x=render(repo=repo,python=Path(sys.executable),state=tmp_path/'data',wrapper=tmp_path/'bin/collector')
    assert f'OnCalendar={CALENDAR}' in x['timer']
    assert 'Persistent=false' in x['timer']
    assert '--raw-dir' in x['wrapper']
    assert 'ExecStart=' in x['service'] and 'X-MBX-APIKEY' not in x['service']

@pytest.mark.skipif(os.name == 'nt', reason='POSIX executable permission bits required')
def test_installer_writes_but_does_not_activate_by_default(tmp_path):
    repo=Path(__file__).resolve().parents[1]
    paths=install(repo,Path(sys.executable),tmp_path/'data',tmp_path/'units',tmp_path/'bin/collector')
    assert all(p.is_file() for p in paths.values())
    assert paths['wrapper'].stat().st_mode & 0o777 == 0o700
