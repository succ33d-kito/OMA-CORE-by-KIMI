"""Cheap freeze verification only: no datasets, downloads, outcomes or trading."""
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT = REPO / 'research/edge_discovery/mechanics_v2_1/FREEZE.json'


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def verify(path=DEFAULT, repo=REPO):
    expected = path.with_suffix('.sha256').read_text().split()[0]
    if digest(path) != expected:
        raise ValueError('freeze hash mismatch; create a reviewed new revision')
    freeze = json.loads(path.read_text(encoding='utf-8'))
    for key in ['evidence_manifest', 'hypothesis_registry']:
        ref = freeze[key]
        target = (repo / ref['path']).resolve()
        if not target.is_relative_to(repo.resolve()) or digest(target) != ref['sha256']:
            raise ValueError(f'{key} provenance mismatch')
    evidence = json.loads((repo / freeze['evidence_manifest']['path']).read_text(encoding='utf-8'))
    classification = freeze['issue_classification']
    if len(classification) != len(evidence['issues']) or {x['issue'] for x in classification} != set(evidence['issues']):
        raise ValueError('every Data Gate issue must have exactly one classification')
    if any(x['category'] not in ['A','B','C','D'] for x in classification):
        raise ValueError('invalid blocker category')
    registry = json.loads((repo / freeze['hypothesis_registry']['path']).read_text(encoding='utf-8'))
    if [h['id'] for h in registry['hypotheses']] != [f'MM-{i:02d}' for i in range(1, 11)]:
        raise ValueError('owner registry identity changed')
    if (freeze['MECHANICS_V2_1_ALLOWED'] or freeze['outcome_testing_allowed']
            or evidence['status'] != 'FAIL' or any(h['status'] != 'BLOCKED' for h in registry['hypotheses'])):
        raise ValueError('this frozen revision admits no experiment; new evidence requires a new freeze')
    return {'freeze_integrity': 'PASS', 'data_gate': 'FAIL', 'experiment': 'BLOCKED',
            'allowed_features': 0, 'ready_hypotheses': 0, 'blocked_hypotheses': 10,
            'outcomes_read': False, 'edge_claim': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true', help='Exit 0 for intact freeze; does NOT authorize outcomes')
    args = parser.parse_args()
    print(json.dumps(verify(), indent=2))
    raise SystemExit(0 if args.verify_only else 2)
