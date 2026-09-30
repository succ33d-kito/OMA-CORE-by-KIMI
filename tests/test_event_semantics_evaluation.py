import copy
import json
from pathlib import Path
import pytest
from scripts.evaluate_event_semantics import set_metrics, categorical, evaluate, predict, text_sha256

ROOT = Path(__file__).resolve().parents[1]


def test_hash_survives_git_newline_conversion(tmp_path):
    a,b = tmp_path/'windows',tmp_path/'unix'
    a.write_bytes(b'line1\r\nline2\r\n')
    b.write_bytes(b'line1\nline2\n')
    assert text_sha256(a) == text_sha256(b)


def test_set_metrics_count_false_positives_and_negatives():
    m = set_metrics([('a',['BTC'],['BTC','ETH']),('b',['SOL'],[]),('c',[],[])])
    assert (m['tp'],m['fp'],m['fn']) == (1,1,1)
    assert m['precision'] == m['recall'] == m['micro_f1'] == .5
    assert m['exact_match'] == 1/3


def test_empty_predictions_do_not_get_perfect_precision():
    m = set_metrics([('a',['SEC'],[])])
    assert m['precision'] is None and m['recall'] == m['micro_f1'] == 0


def test_confusion_matrix_and_macro_f1():
    m = categorical([('a','neutral','neutral'),('b','bullish','neutral')])
    assert m['accuracy'] == .5
    assert m['macro_f1'] == pytest.approx(1/3)
    assert m['confusion_matrix']['bullish']['neutral'] == 1


def test_reference_labels_cannot_influence_predictions():
    r = json.loads((ROOT/'research/event_intelligence/baseline_v1/REFERENCE.json').read_text())
    inputs = [{k:c[k] for k in ('id','title','summary')} for c in r['cases']]
    first = predict(inputs)
    changed = copy.deepcopy(r)
    for c in changed['cases']:
        c['reference'] = {'unrelated':'not classifier input'}
    assert predict([{k:c[k] for k in ('id','title','summary')} for c in changed['cases']]) == first
    assert r['human_reviewed'] is False
    m = evaluate(r,first)
    assert m['sentiment']['n'] == 22
    assert m['sentiment']['excluded_mixed_ids'] == ['M03','M06']
    assert m['event_type_single_label']['n'] == 22
    assert m['entities']['recall'] == 0
    with pytest.raises(ValueError,match='IDs'):
        evaluate(r,first[:-1])
