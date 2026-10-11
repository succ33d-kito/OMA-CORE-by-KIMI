"""Independent replay reconciliation. Reproducibility is not economic truth."""
from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .causal_replay import replay_causal_state
from .causal_observation_snapshot import BTC_CAUSAL_FEATURES
from .prospective_receipts import canonical_observation, observation_hash


@dataclass(frozen=True, slots=True)
class ReplayReconciliationCertificate:
    canonical_json: str

    def to_dict(self):
        return json.loads(self.canonical_json)

    @property
    def status(self):
        return self.to_dict()['status']

    @property
    def reconciliation_id(self):
        return observation_hash(self.to_dict())

    def require_match(self):
        if self.status != 'MATCH':
            raise ValueError('replay reconciliation MISMATCH')
        return self


def _compare(first, second, features):
    left, right = first.to_dict(), second.to_dict()
    fields = sorted(set(left) | set(right))
    differences = [key for key in fields if key not in left or key not in right
                   or canonical_observation(left[key]) != canonical_observation(right[key])]
    return ReplayReconciliationCertificate(canonical_observation({
        'schema':'replay-reconciliation-certificate-v1',
        'status':'MISMATCH' if differences else 'MATCH',
        'feature_contract':list(features),
        'left':left, 'right':right, 'different_fields':differences,
        'meaning':'DETERMINISTIC_RECONSTRUCTION_ONLY',
    }))


def reconcile_causal_replay(ledger, *, instrument, as_of, features=BTC_CAUSAL_FEATURES, dataset_role=None):
    """Two executions, same explicit contract, separate fresh graph stores.

    Source ledger remains read-only. Valid later evidence cannot alter historical
    identity. Concurrent changes affecting the cutoff produce MISMATCH or an
    exception, never a normalized match. Exceptions return no certificate.
    Temporary paths and current ledger head are intentionally not commitments.
    """
    features = tuple(features)  # Consume a caller iterator exactly once.
    with TemporaryDirectory(prefix='oma-replay-reconciliation-') as directory:
        root = Path(directory)
        first = replay_causal_state(ledger,root/'a'/'graph.db',instrument=instrument,
                                    as_of=as_of,features=features,dataset_role=dataset_role)
        second = replay_causal_state(ledger,root/'b'/'graph.db',instrument=instrument,
                                     as_of=as_of,features=features,dataset_role=dataset_role)
        return _compare(first,second,features)
