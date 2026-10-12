"""Experiment 51 synthetic preparation ONLY. No real-data execution entrypoint.

Kernel/CommonSupport remain the population authority. The synthetic smoke path
has no user data, paths, networks or outcomes arguments. It does not authorize
operational gates or adapt reference votes to real features.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import random
from statistics import mean


def commitment(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load_protocol():
    path = Path(__file__).resolve().parents[2] / 'docs' / 'EXPERIMENT_51_PREREGISTRATION.json'
    return json.loads(path.read_text(encoding='utf-8-sig'))


def bind_support(registry):
    """Consume the existing registry, never caller-created support booleans."""
    from .common_support import CommonSupportRegistry
    if type(registry) is not CommonSupportRegistry:
        raise TypeError('CommonSupportRegistry required')
    records = tuple(sorted(registry.records(), key=lambda r: r.opportunity_id))
    if not records or len({r.dataset_role for r in records}) != 1:
        raise ValueError('nonempty single-role population required')
    # Retain every excluded member in the commitment; no selective arm deletion.
    body = tuple((r.opportunity_id, r.support_id, r.cs4) for r in records)
    return commitment(body), tuple(r.opportunity_id for r in records if r.cs4)


def _paired(population, arms):
    if type(population) is not tuple or len(set(population)) != len(population) or not population:
        raise ValueError('unique nonempty frozen population required')
    if set(arms) != {'P0','PR','PM','PRM'}:
        raise ValueError('four arms required')
    if any(set(values) != set(population) for values in arms.values()):
        raise ValueError('identical population required')
    return {name: tuple(values[k] - arms['P0'][k] for k in population) for name, values in arms.items() if name != 'P0'}


def _basic_intervals(calendar, spec):
    """Paired calendar blocks; each hour contains zero or more 3-arm differences."""
    length, block = len(calendar), spec['block_hours']
    original = [row for hour in calendar for row in hour]
    if length < block or not original:
        raise ValueError('insufficient calendar support')
    observed = tuple(mean(row[j] for row in original) for j in range(3))
    rng = random.Random(spec['seed'])
    samples = [[] for _ in range(3)]
    for _ in range(spec['resamples']):
        hours = []
        while len(hours) < length:
            start = rng.randrange(length - block + 1)
            hours.extend(calendar[start:start+block])
        rows = [row for hour in hours[:length] for row in hour]
        if not rows:
            raise ValueError('empty bootstrap support: inconclusive')
        for j in range(3):
            samples[j].append(mean(row[j] for row in rows))
    tail = spec['familywise_alpha'] / (2 * spec['primary_family_size'])
    def quantile(values, q):
        values = sorted(values)
        index = (len(values)-1)*q
        low = int(index)
        high = min(low+1, len(values)-1)
        return values[low] + (index-low)*(values[high]-values[low])
    return tuple(None if len(set(values)) < 2 else
                 (2*observed[j]-quantile(values,1-tail), 2*observed[j]-quantile(values,tail))
                 for j, values in enumerate(samples))


@dataclass(frozen=True, slots=True)
class SyntheticReceipt:
    canonical_json: str

    @property
    def receipt_id(self):
        return sha256(self.canonical_json.encode()).hexdigest()


def synthetic_smoke():
    """Fixed deterministic toy values; explicitly not real experiment evidence."""
    protocol = load_protocol()
    ids = tuple('SYNTHETIC:' + str(i) for i in range(336))
    cost = protocol['cost_model']['round_trip_bps']
    arms = {name: {} for name in protocol['policies']}
    for i, identity in enumerate(ids):
        label_bps = (i % 13) - 6  # manufactured fixture, not market data
        for j, name in enumerate(arms):
            action = ((i+j) % 3) - 1
            arms[name][identity] = action*label_bps - (cost if action else 0)
    paired = _paired(ids, arms)
    calendar = tuple((tuple(paired[name][i] for name in ('PR','PM','PRM')),) for i in range(len(ids)))
    intervals = _basic_intervals(calendar, protocol['uncertainty'])
    body = dict(schema='experiment51-synthetic-receipt-v1', evidence_kind='SYNTHETIC_ONLY',
                protocol_id=commitment(protocol), population_id=commitment(ids),
                paired_mean_bps={name:mean(values) for name,values in paired.items()},
                simultaneous_intervals=intervals, real_experiment=False, policy_winner=None,
                research_verdict='NOT_EVALUATED_SYNTHETIC', edge='NOT_DEMONSTRATED')
    return SyntheticReceipt(json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False))
