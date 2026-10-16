import json, os, subprocess, sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
keys = ['REGIME_DERIVATION_RULE_HASH', 'MECHANICS_TAKER_DERIVATION_RULE_HASH', 'DERIVED_SNAPSHOT_SCHEMA_HASH', 'DERIVED_ADMISSION_RULE_HASH']
if len(sys.argv) > 1:
    sys.path.insert(0, str(repo))
    import core.scientific.derived_snapshot_admission as d
    if sys.argv[1] == 'old':
        source = subprocess.check_output(['git', '-C', str(repo), 'show', '79fea8788097a51ce76d6bcd6403e7223f6b522c:core/scientific/derived_snapshot_admission.py'], text=True)
        # Execute only the historical definitions in memory; no admission function is called.
        exec(compile(source, '<historical-binding>', 'exec'), d.__dict__)
    print(json.dumps({**{k: getattr(d, k) for k in keys}, 'BUNDLE_COMMITMENT': d.bundle_commitment()}))
else:
    result = {}
    for mode in ('old', 'new'):
        result[mode] = {}
        for seed in ('0', '1', '7', '42', '12345', 'random'):
            env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE='1')
            result[mode][seed] = json.loads(subprocess.check_output([sys.executable, '-B', __file__, mode], env=env, text=True))
    for key in keys + ['BUNDLE_COMMITMENT']:
        old = len({r[key] for r in result['old'].values()})
        new = len({r[key] for r in result['new'].values()})
        assert new == 1, (key, new)
        print(key, 'OLD_DISTINCT=', old, 'NEW_DISTINCT=', new)
    (repo / 'docs' / 'EXPERIMENT_51_REGIME_HASH_PROCESS_EVIDENCE.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['new']['1'], indent=2))
    import itertools
    sys.path.insert(0, str(repo))
    import core.scientific.derived_snapshot_admission as d
    targets = {'schema': 'e041b7ada8f75ca7cb8f29a033bad9cddbadbbeb4629eea08157d90de79683da', 'mechanics': '33adaea7d3f4539ffed8c4f444c6b841ef886b87deab4f77acff21d2038a4e91', 'bundle': 'f839f63d391fcd61064be1256b6d4e7755f976456c0fc309c1a37be38e6ddcae'}
    matches = {k: [] for k in targets}
    for features in itertools.permutations(d.BUNDLE_FEATURES):
        schema = d.digest((d.REGIME_DERIVED_SCHEMA, d.MECHANICS_DERIVED_SCHEMA, d.REGIME_FEATURE, d.MECHANICS_FEATURE, d.WINDOW_SCHEMA, features))
        mechanics = d.digest((d.MECHANICS_TAKER_DERIVATION_RULE_ID, d.MECHANICS_DERIVED_SCHEMA, d.MECHANICS_FEATURE, features, d.EXP51_MECHANICS_INPUTS, d.DERIVED_AVAILABILITY_RULE))
        bundle = d.commitment_bundle()
        bundle.update(atomic_bundle_features=features, derived_snapshot_schema_hash=schema, mechanics_taker_derivation_rule_hash=mechanics)
        for key, value in {'schema': schema, 'mechanics': mechanics, 'bundle': d.digest(bundle)}.items():
            if value == targets[key]:
                matches[key].append(features)
    assert all(matches.values()), matches
    print('EXACT_HISTORICAL_VALUES_REPRODUCED', json.dumps(matches))
