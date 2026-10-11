from datetime import timedelta
import json
import pytest
from scripts import reconcile_causal_replay as cli
from core.scientific.replay_reconciliation import ReplayReconciliationCertificate
from tests.test_causal_replay import prepare_ledger
from tests.test_metrics_continuity import state,S


def args(ledger,output):
    return ['--ledger',str(ledger),'--output',str(output),'--instrument','BTCUSDT',
            '--as-of',(S+timedelta(minutes=5)).isoformat()]


def test_real_export_and_no_overwrite(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path); before=ledger.read_bytes(); output=tmp_path/'certificate.json'
    assert cli.main(args(ledger,output))==0
    raw=output.read_bytes(); assert json.loads(raw)['status']=='MATCH'
    assert ledger.read_bytes()==before
    with pytest.raises(FileExistsError): cli.main(args(ledger,output))
    assert output.read_bytes()==raw


def test_mismatch_is_exported_with_nonzero_exit(state,tmp_path,monkeypatch):
    ledger=prepare_ledger(state,tmp_path); output=tmp_path/'mismatch.json'
    certificate=ReplayReconciliationCertificate('{"status":"MISMATCH","different_fields":["snapshot_id"]}')
    monkeypatch.setattr(cli,'reconcile_causal_replay',lambda *a,**k:certificate)
    assert cli.main(args(ledger,output))==2
    assert json.loads(output.read_bytes())['different_fields']==['snapshot_id']


def test_reconstruction_error_produces_no_output(state,tmp_path,monkeypatch):
    ledger=prepare_ledger(state,tmp_path); output=tmp_path/'error.json'
    def fail(*a,**k): raise ValueError('invalid evidence')
    monkeypatch.setattr(cli,'reconcile_causal_replay',fail)
    with pytest.raises(ValueError): cli.main(args(ledger,output))
    assert not output.exists()


def test_naive_cutoff_rejected_before_output(state,tmp_path):
    ledger=prepare_ledger(state,tmp_path); output=tmp_path/'naive.json'
    values=args(ledger,output); values[-1]='2026-10-11T13:05:00'
    with pytest.raises(ValueError,match='aware'): cli.main(values)
    assert not output.exists()


def test_missing_ledger_not_created(tmp_path):
    ledger=tmp_path/'missing.db'; output=tmp_path/'missing.json'
    with pytest.raises(FileNotFoundError): cli.main(args(ledger,output))
    assert not ledger.exists() and not output.exists()
