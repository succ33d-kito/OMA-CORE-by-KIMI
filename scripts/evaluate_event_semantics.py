"""Offline diagnostic reference evaluation; never collects news or writes a DB."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.collectors.rss_collector import RSSCollector


def text_sha256(path):
    """Stable across Git's Windows/Unix newline conversions."""
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def set_metrics(pairs):
    tp = fp = fn = exact = 0
    errors = []
    for identity, expected, predicted in pairs:
        expected, predicted = set(expected), set(predicted)
        tp += len(expected & predicted)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        exact += expected == predicted
        if expected != predicted:
            errors.append(dict(id=identity, false_positive=sorted(predicted-expected), false_negative=sorted(expected-predicted)))
    return dict(n=len(pairs), tp=tp, fp=fp, fn=fn,
        precision=tp/(tp+fp) if tp+fp else None,
        recall=tp/(tp+fn) if tp+fn else None,
        micro_f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
        exact_match=exact/len(pairs) if pairs else None, errors=errors)


def categorical(pairs):
    labels = sorted(set(x for _, a, b in pairs for x in (a,b)))
    per_class = {}
    matrix = {a:{b:0 for b in labels} for a in labels}
    for _, a, b in pairs:
        matrix[a][b] += 1
    for label in labels:
        scores = set_metrics([(i,[a] if a == label else [],[b] if b == label else []) for i,a,b in pairs])
        per_class[label] = {k:v for k,v in scores.items() if k not in ('errors','exact_match','n')}
        per_class[label]['support'] = sum(a == label for _,a,_ in pairs)
    supported = [v for v in per_class.values() if v['support']]
    return dict(n=len(pairs), accuracy=sum(a==b for _,a,b in pairs)/len(pairs) if pairs else None,
        macro_f1=sum(v['micro_f1'] or 0 for v in supported)/len(supported) if supported else None,
        confusion_matrix=matrix, per_class=per_class)


def predict(cases):
    # The production RSS parsing path supplies assets, sentiment AND default entities.
    # No reference label is passed to the classifier, and no network is possible.
    collector = RSSCollector(sources=['rss_bloomberg'])
    output = []
    for case in cases:
        collector.feedparser = SimpleNamespace(parse=lambda _, c=case:SimpleNamespace(
            entries=[{'title':c['title'],'summary':c['summary']}], feed={'title':'offline reference'}))
        events = collector.collect()
        if len(events) != 1:
            raise ValueError('reference case did not produce exactly one event: '+case['id'])
        e = events[0]
        output.append(dict(id=case['id'],event_types=[e.event_type.value],
            assets=sorted({a.symbol for a in e.assets}), entities=sorted(set(e.entities)),
            sentiment=e.sentiment.name.lower(), sentiment_score=e.sentiment_score))
    return output


def evaluate(reference, predictions):
    cases = reference['cases']
    by_id = {p['id']:p for p in predictions}
    ids = [c['id'] for c in cases]
    if len(set(ids)) != len(ids) or len(by_id) != len(predictions) or set(ids) != set(by_id):
        raise ValueError('duplicate or mismatched IDs')
    metrics = {}
    for dimension in ('event_types','assets','entities'):
        metrics[dimension] = set_metrics([(c['id'],c['reference'][dimension],by_id[c['id']][dimension]) for c in cases])
    metrics['event_type_single_label'] = categorical([(c['id'],c['reference']['event_types'][0],by_id[c['id']]['event_types'][0]) for c in cases if len(c['reference']['event_types']) == 1])
    sentiment_pairs = [(c['id'],c['reference']['sentiment'],by_id[c['id']]['sentiment']) for c in cases if c['reference']['sentiment'] is not None]
    metrics['sentiment'] = categorical(sentiment_pairs)
    metrics['sentiment']['coverage'] = len(sentiment_pairs)/len(cases)
    metrics['sentiment']['excluded_mixed_ids'] = [c['id'] for c in cases if c['reference']['sentiment'] is None]
    metrics['sentiment']['errors'] = [dict(id=i, expected=a,predicted=b) for i,a,b in sentiment_pairs if a != b]
    metrics['entities']['capability'] = 'NOT_IMPLEMENTED_IN_RSS; actual Event.entities default is empty'
    tags = sorted({t for c in cases for t in c['tags']})
    metrics['slices'] = {}
    for tag in tags:
        selected = [c for c in cases if tag in c['tags']]
        metrics['slices'][tag] = dict(n=len(selected),event_exact_match=sum(c['reference']['event_types']==by_id[c['id']]['event_types'] for c in selected)/len(selected),
            sentiment=categorical([(c['id'],c['reference']['sentiment'],by_id[c['id']]['sentiment']) for c in selected if c['reference']['sentiment'] is not None]))
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=ROOT/'research/event_intelligence/baseline_v1/REFERENCE.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.reference.read_bytes()
    reference = json.loads(raw)
    predictions = predict([{k:c[k] for k in ('id','title','summary')} for c in reference['cases']])
    report = dict(schema='event-semantic-evaluation-v1', reference_sha256=text_sha256(args.reference),
        hash_policy='UTF-8 text; CRLF and CR normalized to LF',
        classifier_sha256=text_sha256(ROOT/'core/collectors/rss_collector.py'),
        evaluator_sha256=text_sha256(__file__),
        label_status=reference['label_status'], human_reviewed=reference['human_reviewed'],
        baseline_commit='63dcb70a45b632f97fea20525117e1dc0d4c8d6c',
        metrics=evaluate(reference,predictions))
    args.output.mkdir(parents=True,exist_ok=True)
    for name, body in [('PREDICTIONS.json',predictions),('METRICS.json',report)]:
        (args.output/name).write_text(json.dumps(body,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:{m:v for m,v in data.items() if m in ('n','precision','recall','micro_f1','exact_match','accuracy','macro_f1','coverage')} for k,data in report['metrics'].items() if k != 'slices'},indent=2))


if __name__ == '__main__':
    main()
