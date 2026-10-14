from datetime import datetime,timedelta
import inspect
import shutil
from pathlib import Path
import json
import socket
import sqlite3
import pytest
from core.scientific import metrics_admission_operator as op
from core.scientific import metrics_observation_admission as admission
from core.scientific import metrics_publication as publication
from core.scientific.prospective_receipts import canonical_observation,observation_hash
from core.scientific.experiment51_derived import derived
from tests.test_metrics_continuity import state,S,capture


def files(root): return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.fixture
def setup(state,tmp_path,monkeypatch):
    clock=[S-timedelta(minutes=10)]
    monkeypatch.setattr(op,'_now',lambda:clock[0])
    monkeypatch.setattr(publication,'_now',lambda:clock[0])
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None): return clock[0]
    monkeypatch.setattr(admission,'datetime',Clock)
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('worker must not use network'))
    a=op.MetricsAdmissionAuthorityV1.activate(tmp_path/'admission',state[0],environment='TEST_ONLY')
    return a,clock,state


def test_activation_internal_exclusive_and_no_backdate(setup):
    a,clock,state=setup
    assert a.body['activated_at']==clock[0].isoformat()
    assert 'activated_at' not in inspect.signature(a.activate).parameters
    before=files(a.root)
    with pytest.raises(FileExistsError): a.activate(a.root,state[0],environment='TEST_ONLY')
    with pytest.raises(TypeError): a.activate(a.root,state[0],environment='TEST_ONLY',activated_at=S)
    assert files(a.root)==before


@pytest.mark.parametrize('field',['dataset_role','capture_contract_hash','admission_contract_hash',
    'durable_publication_contract_hash','source_state_binding','observations_v2_binding','authority_id','contract_hash','runtime_commit'])
def test_corrupt_or_conflicting_authority_fails_closed(setup,field):
    a,_,_=setup;b=a.body;b[field]='wrong'
    (a.root/'authority.json').write_text(canonical_observation(b))
    with pytest.raises((ValueError,OSError,KeyError)): op.MetricsAdmissionAuthorityV1(a.root)


def test_wrong_role_and_production_fixture_rejected(state,tmp_path):
    with pytest.raises(ValueError,match='PILOT'): op.MetricsAdmissionAuthorityV1.activate(tmp_path/'a',state[0],role='DISCOVERY',environment='TEST_ONLY')
    with pytest.raises(ValueError): op.MetricsAdmissionAuthorityV1.activate(tmp_path/'b',state[0])
    with pytest.raises(ValueError,match='test authority'): op._deployment(op.PRODUCTION/'metrics-admission-v1',state[0],'TEST_ONLY')
    with pytest.raises(ValueError,match='test authority'): op._deployment(tmp_path/'a',op.PRODUCTION/'metrics-h1-v1','TEST_ONLY')


def test_pre_authority_complete_capture_never_admitted(state,tmp_path,monkeypatch):
    capture(state);monkeypatch.setattr(op,'_now',lambda:S+timedelta(minutes=4))
    a=op.MetricsAdmissionAuthorityV1.activate(tmp_path/'admission',state[0],environment='TEST_ONLY')
    before=files(state[0]);result=a.once()
    assert result['status']=='NO_ELIGIBLE_BUNDLES' and result['pre_authority_valid']==1
    assert not (a.root/'observations.sqlite').exists()
    assert files(state[0])==before


def test_complete_future_capture_publication_taker_mechanics_idempotent(setup):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=4)
    before=files(state[0]);first=a.once();r=first['results'][0]
    assert r['status']=='ADMITTED' and len(r['observation_ids'])==6
    ledger=a.body['observations_v2_binding'];rows,_=publication.observation_snapshot(ledger)
    p=publication.publication_for(rows,r['bundle_id'])
    assert p['publication_id']==r['publication_id'] and p['published_at']==clock[0].isoformat()
    view=derived(ledger,role='PILOT',decision_at=S+timedelta(hours=1),mechanics_id=r['mechanics_id'])
    assert view.taker=='1.4'
    raw=Path(ledger).read_bytes()
    clock[0]+=timedelta(seconds=1);second=a.once()
    assert second['results'][0]['status']=='ALREADY_ADMITTED'
    assert Path(ledger).read_bytes()==raw
    assert files(state[0])==before
    status=a.status()
    assert status['POST_AUTHORITY_ATOMIC_BUNDLES_ADMITTED']==1
    assert status['MECHANICS_REAL_PATH_OBSERVED'] is False # fixtures cannot claim real path
    assert status['METRICS_REAL_READY'] is status['EXPERIMENT_51_READY'] is False


def test_empty_scan_and_readonly_status(setup):
    a,clock,state=setup;clock[0]=S+timedelta(minutes=4)
    assert a.once()['status']=='NO_ELIGIBLE_BUNDLES'
    before=files(a.root);source=files(state[0]);r=a.status()
    assert r['POST_AUTHORITY_ATOMIC_BUNDLES_ADMITTED']==0
    assert files(a.root)==before and files(state[0])==source


@pytest.mark.parametrize('mutation',['FAILED','MISSED_SLOT','INCOMPLETE','INVALID','corrupt_raw','missing_raw','partial_values'])
def test_invalid_capture_never_admitted(setup,mutation):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=4)
    root=state[0]/'attempts'/'20261011T130000Z'
    if mutation=='MISSED_SLOT':
        # Only disposable test fixture; never production state.
        shutil.rmtree(root)
    elif mutation=='INCOMPLETE': (root/'result.json').unlink()
    elif mutation=='missing_raw': (root/'capture'/'raw'/'oi.json').unlink()
    elif mutation=='corrupt_raw': (root/'capture'/'raw'/'oi.json').write_text('[]')
    elif mutation=='partial_values':
        path=root/'capture'/'receipt.json';data=json.loads(path.read_text());data['normalized_metrics'].pop(next(iter(data['normalized_metrics'])));path.write_text(json.dumps(data))
    else:
        path=root/'result.json';data=json.loads(path.read_text());data['status']=mutation;path.write_text(json.dumps(data))
    assert a.once()['status']=='NO_ELIGIBLE_BUNDLES'
    assert not (a.root/'observations.sqlite').exists()


def test_failure_after_claim_is_terminal_no_retry(setup,monkeypatch):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=4)
    monkeypatch.setattr(op,'admit_verified_metrics_bundle',lambda *a,**k:(_ for _ in ()).throw(ValueError('injected failure')))
    assert a.once()['results'][0]['status']=='FAILED_VALIDATION'
    assert a.once()['results'][0]['status']=='TERMINAL_OR_INCOMPLETE_NO_RETRY'
    assert not (a.root/'observations.sqlite').exists()


def test_publication_failure_does_not_repair(setup,monkeypatch):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=4)
    monkeypatch.setattr(publication,'_publish_committed',lambda *a:(_ for _ in ()).throw(ValueError('publication fault')))
    r=a.once()['results'][0]
    assert r['status']=='PUBLICATION_OR_DERIVATION_FAILED_NO_REPAIR'
    rows,_=publication.observation_snapshot(a.body['observations_v2_binding'])
    assert len(rows)==6 and not rows._receipts
    assert a.once()['results'][0]['status']=='TERMINAL_OR_INCOMPLETE_NO_RETRY'
    assert a.status()['POST_AUTHORITY_ATOMIC_BUNDLES_ADMITTED']==0


def test_duplicate_claim_and_journal_tamper_fail_closed(setup):
    a,_,_=setup;a._append('START',{'slot':S.isoformat()},claim=True)
    with pytest.raises(ValueError,match='already claimed'): a._append('START',{'slot':S.isoformat()},claim=True)
    with sqlite3.connect(a.root/'attempts.sqlite') as con:
        with pytest.raises(sqlite3.DatabaseError,match='append-only'): con.execute('DELETE FROM entries')
        con.execute('DROP TRIGGER journal_no_update');con.execute("UPDATE entries SET hash='bad'")
    with pytest.raises(ValueError,match='integrity'): a.status()


def test_late_publication_no_timely_mechanics(setup):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=6)
    result=a.once()['results'][0]
    assert result['status']=='ADMITTED' and result['mechanics_id'] is None
    assert result['mechanics_reason']=='PUBLICATION_AFTER_FROZEN_RAW_CUTOFF'
    assert a.status()['METRICS_REAL_READY'] is False


def test_post_authority_later_hour_admitted_without_backdating(setup):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(hours=1,minutes=4)
    result=a.once()['results'][0]
    assert result['status']=='ADMITTED'
    assert result['published_at']==clock[0].isoformat()
    assert result['mechanics_id'] is None
    rows,_=publication.observation_snapshot(a.body['observations_v2_binding'])
    from core.scientific.metrics_snapshot_gate import metrics_snapshot_available
    assert not any(metrics_snapshot_available(rows,i,S+timedelta(hours=1)) for i in rows)
    assert all(metrics_snapshot_available(rows,i,clock[0]) for i in rows)
    assert a.once()['results'][0]['status']=='ALREADY_ADMITTED'


def test_cli_does_not_offer_fixture_activation():
    import scripts.metrics_admission as cli
    with pytest.raises(SystemExit): cli.main(['--root','unused','activate','--capture-root','unused','--environment','TEST_ONLY'])


def test_scheduler_duplicate_rejected_before_registration():
    import os,subprocess
    from pathlib import Path
    if os.name!='nt': pytest.skip('Windows Task Scheduler boundary')
    script=Path(__file__).resolve().parents[1]/'scripts'/'install_metrics_admission_task.ps1'
    command="function Get-ScheduledTask { [pscustomobject]@{TaskName='existing'} }; & '"+str(script)+"' -QualifiedCommit '"+'a'*40+"'"
    result=subprocess.run([shutil.which('pwsh') or 'powershell','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True)
    assert result.returncode!=0 and 'already exists' in result.stderr


def test_transaction_failure_has_no_publication_or_partial_rows(setup):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=4)
    from core.scientific.prospective_receipts import observation_snapshot as physical
    ledger=a.body['observations_v2_binding'];physical(ledger)
    with sqlite3.connect(ledger) as con:
        con.execute("CREATE TRIGGER fault BEFORE INSERT ON observations_v2 WHEN (SELECT count(*) FROM observations_v2)=3 BEGIN SELECT RAISE(ABORT,'test fault'); END")
    assert a.once()['results'][0]['status']=='FAILED_VALIDATION'
    assert physical(ledger,read_only=True)[0]=={}


def test_conflicting_existing_rows_are_not_upgraded(setup):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(minutes=4)
    r=a.once()['results'][0];ledger=a.body['observations_v2_binding']
    with sqlite3.connect(ledger) as con:
        con.execute('DROP TRIGGER observations_v2_no_update')
        con.execute("UPDATE observations_v2 SET body='{}' WHERE id=?",(r['observation_ids'][0],))
    with pytest.raises(ValueError): a.once()


def test_later_completed_capture_can_be_reinspected(setup):
    a,clock,state=setup;clock[0]=S+timedelta(minutes=4)
    assert a.once()['status']=='NO_ELIGIBLE_BUNDLES'
    capture(state);clock[0]=S+timedelta(minutes=9)
    r=a.once()['results'][0]
    assert r['status']=='ADMITTED' and r['published_at']==clock[0].isoformat()
    assert r['mechanics_id'] is None


def test_receipt_request_boundary_not_economic_period(state,tmp_path,monkeypatch):
    clock=[S+timedelta(minutes=1)]
    monkeypatch.setattr(op,'_now',lambda:clock[0])
    a=op.MetricsAdmissionAuthorityV1.activate(tmp_path/'admission',state[0],environment='TEST_ONLY')
    capture(state);clock[0]=S+timedelta(minutes=4)
    assert a.inventory()[-1]['boundary']=='POST_AUTHORITY_CAPTURE'


def test_test_process_rejects_production_before_read():
    with pytest.raises(ValueError,match='tests cannot access'):
        op.MetricsAdmissionAuthorityV1(op.PRODUCTION/'metrics-admission-v1')


def test_qualified_admission_age_limit_is_preserved(setup):
    a,clock,state=setup;capture(state);clock[0]=S+timedelta(days=1,seconds=1)
    r=a.once()['results'][0]
    assert r['status']=='FAILED_VALIDATION' and 'backfill' in r['error']
    assert not Path(a.body['observations_v2_binding']).exists()
