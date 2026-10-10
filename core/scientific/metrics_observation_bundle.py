"""Read-only verified Metrics projection. No observations_v2 admission yet.

The immutable envelope retains all six values and their common capture authority.
Capture availability is provenance, not ledger availability or decision eligibility.
"""
from dataclasses import dataclass
from pathlib import Path

from . import metrics_h1_runner as runner
from . import metrics_h1_activation as activation
from . import metrics_continuity as continuity


@dataclass(frozen=True)
class VerifiedMetricsBundle:
    canonical_json: str

    @property
    def bundle_id(self):
        import hashlib
        return hashlib.sha256(self.canonical_json.encode()).hexdigest()


def load_verified_bundle(state, slot, *, repo_root, now):
    """Project only fully verified SUCCESS; never modifies source or ledger.

    Hashes provide integrity, not cryptographic proof against complete rewrites.
    Consumers must use this loader rather than treating the dataclass constructor
    or its hash as admission authority.
    """
    config = runner.load_config(state,repo_root=repo_root)
    slot, now = runner._slot(slot), runner._utc(now)
    if slot < runner._slot(config['activation_slot']):
        raise ValueError('slot precedes activation')
    path = runner._path(Path(state),slot)
    files = [path/'attempt.json',path/'result.json',path/'capture'/'receipt.json',
             path/'capture'/'available.json',
             *(path/'capture'/'raw'/(key+'.json') for key in config['components'])]

    def snapshot():
        result=[]
        for file in files:
            activation._reject_aliases(file)
            result.append(file.read_bytes())
        return result

    before = snapshot()
    if continuity.verify_slot(state,slot,repo_root=repo_root,now=now)['status'] != 'SUCCESS':
        raise ValueError('verified SUCCESS bundle required')
    attempt, result, receipt, marker = map(continuity._json,before[:4])
    values=[]
    for key, component in sorted(config['components'].items()):
        for raw_field, (normalized_field,feature) in sorted(component['fields'].items()):
            values.append({'feature':feature,'value':receipt['normalized_metrics'][normalized_field],
                           'component':key,'raw_field':raw_field})
    if len(values)!=6 or len({value['feature'] for value in values})!=6:
        raise ValueError('complete six-value projection required')
    envelope={'schema':'metrics-h1-verified-bundle-v1','contract':config['contract'],
              'activation_id':config['activation_id'],'instrument':config['instrument'],
              'provider':config['provider'],'product':config['product'],
              'dataset_role':config['dataset_role'],'slot':slot.isoformat(),
              'slot_id':attempt['slot_id'],'attempt_id':attempt['attempt_id'],
              'result_id':result['result_id'],'capture_receipt_id':receipt['receipt_id'],
              'source_period_start':receipt['source_period_start'],
              'source_period_end':receipt['source_period_end'],
              'received_at':max(runner._utc(c['received_at']) for c in receipt['components'].values()).isoformat(),
              'capture_available_at':marker['available_at'],
              'raw_bundle_sha256':receipt['raw_bundle_sha256'],
              'selected_rows_sha256':receipt['selected_rows_sha256'],
              'components':receipt['components'],'values':values,
              'derived':False,'dependencies':[],
              'ledger_available_at':None,'admission_status':'NOT_ADMITTED'}
    if snapshot()!=before or runner.load_config(state,repo_root=repo_root)!=config:
        raise ValueError('evidence changed during verification')
    return VerifiedMetricsBundle(activation._canonical(envelope).decode())
