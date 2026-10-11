"""Read-only consistency gate for already admitted six-member Metrics bundles.

Reconstructs the admitted bundle commitment, not raw provider truth. The trusted
capture/admission boundary remains required; full local forgery is outside hashes.
"""
from .metrics_observation_admission import (
    ADMISSION_CONTRACT, EXPECTED_MAPPING, EXPECTED_FEATURES,
    _parse_verified_bundle, _build_items,
)
from .metrics_observation_bundle import VerifiedMetricsBundle
from .prospective_receipts import canonical_observation, observation_hash, _utc


def metrics_snapshot_available(rows, identity, as_of):
    try:
        item=rows[identity]; p=item['provenance']; cutoff=_utc(as_of)
        if p['contract']!=ADMISSION_CONTRACT or item['feature'] not in EXPECTED_FEATURES:
            return False
        bundle_id=p['bundle_id']
        members=[x for x in rows.values() if x.get('provenance',{}).get('bundle_id')==bundle_id]
        if len(members)!=6 or {x['feature'] for x in members}!=EXPECTED_FEATURES:
            return False
        by_feature={x['feature']:x for x in members}
        admitted=_utc(item['available_at'])
        if admitted>cutoff: return False
        if p['dataset_role'] not in ('PILOT','DISCOVERY','CONFIRMATION'): return False
        body={key:p[key] for key in (
            'activation_id','provider','product','dataset_role','slot','slot_id','attempt_id',
            'result_id','capture_receipt_id','source_period_start','source_period_end',
            'capture_available_at','raw_bundle_sha256','selected_rows_sha256')}
        body.update(schema=p['bundle_schema'],contract=p['capture_contract'],
                    instrument=item['instrument'],received_at=p['capture_received_at'],
                    derived=False,dependencies=[],ledger_available_at=None,admission_status='NOT_ADMITTED')
        components={}; values=[]
        for (component,raw_field),feature in sorted(EXPECTED_MAPPING.items()):
            member=by_feature[feature]
            meta=member['provenance']['component_metadata']
            if component in components and canonical_observation(components[component])!=canonical_observation(meta):
                return False
            components[component]=meta
            values.append(dict(feature=feature,value=member['payload']['value'],
                               component=component,raw_field=raw_field))
        body.update(components=components,values=values)
        bundle=VerifiedMetricsBundle(canonical_observation(body))
        if bundle.bundle_id!=bundle_id: return False
        _parse_verified_bundle(bundle)
        expected=_build_items(body,bundle_id,admitted)
        for row in expected:
            actual=rows.get(row['id'])
            if canonical_observation(actual)!=canonical_observation(row): return False
        return identity in {x['id'] for x in expected}
    except (KeyError,TypeError,ValueError,OverflowError,AttributeError):
        return False
