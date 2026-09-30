import hashlib
from pathlib import Path
import pandas as pd
import pytest
from scripts import confirm_2024_metrics as c

@pytest.fixture
def synthetic_source(tmp_path, monkeypatch):
    """Test the legacy mixed-year schema without opening real holdout prices."""
    p = tmp_path / 'synthetic_source.csv'
    pd.DataFrame({'Date': pd.date_range('2024-01-01', periods=17544, freq='h').strftime('%d-%m-%Y %H:%M'),
                  'Open': 100., 'High': 101., 'Low': 99., 'Close': 100., 'Volume': 1.}).to_csv(p, index=False)
    blob = hashlib.sha1(f'blob {p.stat().st_size}\0'.encode() + p.read_bytes()).hexdigest()
    monkeypatch.setattr(c, 'BLOB', blob)
    return p

def test_2024_source_strict_validation(tmp_path, synthetic_source):
    source=synthetic_source
    clean,manifest=c.validate(source,tmp_path)
    assert len(clean)==8784
    assert manifest['duplicates']==manifest['gaps']==manifest['invalid_ohlcv']==0
    assert manifest['normalized_sha256']==c.sha(tmp_path/'BTCUSDT_USDM_H1_2024.csv')

def test_duplicate_hour_rejected_before_ablation(tmp_path,monkeypatch,synthetic_source):
    source=synthetic_source
    d=pd.read_csv(source);d.loc[1,'Date']=d.loc[0,'Date'];bad=tmp_path/'bad.csv';d.to_csv(bad,index=False)
    blob=hashlib.sha1(f'blob {bad.stat().st_size}\0'.encode()+bad.read_bytes()).hexdigest()
    monkeypatch.setattr(c,'BLOB',blob)
    with pytest.raises(ValueError,match='8784 unique contiguous'):
        c.validate(bad,tmp_path/'out')


def test_changed_source_hash_rejected(tmp_path, synthetic_source):
    synthetic_source.write_bytes(synthetic_source.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='Git blob mismatch'):
        c.validate(synthetic_source, tmp_path/'out')

def test_official_checksum_tamper_rejected(tmp_path):
    import shutil
    source=Path(__file__).resolve().parents[1]/'research/metrics_2024_2025/official_2024'
    shutil.copytree(source,tmp_path/'official')
    check=tmp_path/'official/BTCUSDT-1h-2024-01.zip.CHECKSUM'
    check.write_text('0'*64+'  BTCUSDT-1h-2024-01.zip\n')
    clean=pd.read_csv(Path(__file__).resolve().parents[1]/'research/metrics_2024_2025/BTCUSDT_USDM_H1_2024.csv')
    with pytest.raises(ValueError,match='official checksum mismatch'):
        c.official_compare(clean,tmp_path/'official',tmp_path)
