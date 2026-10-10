"""Static design qualification; no network, activation, journal or outcomes."""
import hashlib
import json
from pathlib import Path

from core.market_mechanics.binance_live_adapter import METRIC_ENDPOINTS

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'docs/METRICS_H1_RUNTIME_DESIGN.json'
D = json.loads(DESIGN.read_bytes())
PREREG_SHA = '012a80dcfd4566c7906c61a03f2c5ce3991c31481d2bdb4d87e6855d6005bc46'


def test_canonical_design_and_version():
    assert DESIGN.read_bytes() == json.dumps(D, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    assert D['schema'] == 'metrics-h1-runtime-design-v1'
    assert D['protocol_contract'] == 'metrics-h1-capture-v1'
    assert D['status'] == 'DESIGN_ONLY'


def test_explicit_external_activation_only():
    a, s = D['activation'], D['state_root_policy']
    assert a['authority'] == 'EXPLICIT_OPERATOR_TRANSACTION'
    assert a['immutable_after_initialize'] is True
    assert all(a[k] is False for k in ('runtime_may_initialize', 'adapter_may_initialize', 'task_installer_may_initialize'))
    assert a['minimum_lead_seconds'] == 600
    assert a['selection_rule'] == 'FIRST_UTC_HOUR_BOUNDARY_AT_OR_AFTER_NOW_PLUS_600_SECONDS'
    assert s['required_leaf'] == 'metrics-h1-v1'
    assert s['template'] == r'%USERPROFILE%\Documents\O-C data\prospective\metrics-h1-v1'
    assert all(s[k] is True for k in ('absolute', 'must_be_outside_repository', 'reject_symlink_reparse', 'resolved_only_during_explicit_activation', 'separate_from_price_funding'))


def test_frozen_window_and_no_repair():
    c = D['capture']
    assert c['cadence'] == 'H1'
    assert (c['target_offset_seconds'], c['deadline_offset_seconds']) == (180, 300)
    assert c['start_window'] == '[TARGET,DEADLINE)'
    assert c['completion_deadline_inclusive'] is True
    assert c['same_slot_retry'] == 'NONE'
    assert all(c[k] is False for k in ('backfill', 'historical_repair', 'interpolation', 'synthetic_availability', 'automatic_http_retries'))
    assert (c['logical_transactions_per_slot'], c['http_responses'], c['economic_values']) == (1, 5, 6)
    assert c['http_451'] == 'FAIL_CLOSED'
    assert c['request_budget'] == 'REMAINING_WINDOW'
    assert c['redirects'] == 'REJECT'


def test_exact_period_not_latest():
    b = D['source_bundle']
    assert b['expected_period_end'] == 'SLOT'
    assert b['normalized_timestamp'] == 'SLOT_MINUS_ONE_MICROSECOND'
    assert b['period_seconds'] == 300
    assert b['complete_required'] is True
    assert b['mixed_periods'] == 'REJECT'
    assert b['older_substitution'] is b['latest_only_selection'] is False
    assert b['alignment'] == 'NEAREST_300_SECONDS_MAX_30_SECONDS_DISPLACEMENT'
    assert b['taker_timestamp_label'] == 'PERIOD_START'
    assert b['other_timestamp_labels'] == 'PERIOD_END'
    assert b['duplicate_matching_rows'] == 'REJECT'


def test_six_features_and_endpoint_mapping():
    assert D['instrument'] == 'BTCUSDT'
    assert D['provider'] == 'https://fapi.binance.com'
    assert D['product'] == 'USD-M'
    assert {k: v['endpoint'] for k, v in D['components'].items()} == METRIC_ENDPOINTS
    assert {k: v['fields'] for k, v in D['components'].items()} == {
        'oi': {'sumOpenInterest': ['sum_open_interest', 'MarketMetrics/OpenInterest'], 'sumOpenInterestValue': ['sum_open_interest_value', 'MarketMetrics/OpenInterestValue']},
        'top_account': {'longShortRatio': ['count_toptrader_long_short_ratio', 'MarketMetrics/TopTraderAccountPositioning']},
        'top_position': {'longShortRatio': ['sum_toptrader_long_short_ratio', 'MarketMetrics/TopTraderPositionPositioning']},
        'global': {'longShortRatio': ['count_long_short_ratio', 'MarketMetrics/GlobalPositioning']},
        'taker': {'buySellRatio': ['sum_taker_long_short_vol_ratio', 'MarketMetrics/TakerBuySellRatio']},
    }


def test_provenance_and_atomic_availability():
    p = D['provenance']
    assert p['raw_payloads'] == 'EXACT_FULL_RESPONSE_BYTES_BASE64'
    assert p['raw_bundle_sha256'] == 'SHA256_CANONICAL_ENDPOINT_TO_RESPONSE_BASE64_MAP'
    assert p['selected_rows_sha256'] == 'EXISTING_NORMALIZER_INPUT_CANONICAL_JSON_SHA256'
    assert set(p['per_component']) == {'endpoint', 'request_parameters', 'http_status', 'raw_timestamp', 'normalized_period_end', 'requested_at', 'received_at', 'raw_response_sha256'}
    assert set(p['bundle']) == {'contract', 'instrument', 'dataset_role', 'slot_id', 'attempt_id', 'result_id', 'source_period_start', 'source_period_end', 'received_at', 'available_at', 'raw_bundle_sha256', 'selected_rows_sha256'}
    assert p['received_at'] == 'MAX_COMPONENT_RECEIVED_AT'
    assert p['available_at'] == 'ACTUAL_DURABLE_BUNDLE_PUBLICATION_TIME'
    assert p['causal_order'] == 'TARGET <= EACH_REQUEST <= EACH_RECEIPT <= AVAILABLE_AT <= DEADLINE'
    assert p['timestamps'] == 'AWARE_UTC_ONLY'
    assert p['partial_admission'] is False
    assert p['identity'] == 'SHA256_CANONICAL_JSON_NO_RANDOM_OR_REPR'
    assert p['role'] == 'EXPLICIT_IMMUTABLE_ACTIVATION_ROLE'


def test_runtime_has_no_other_authority():
    r = D['runtime']
    assert D['task_name'] == 'OMA-CORE-Prospective-Metrics-H1'
    assert r['topology'] == 'LONG_RUNNING_AT_LOGON'
    assert r['heartbeat'] == 'runtime/heartbeat.json'
    assert r['heartbeat_is_evidence'] is False
    assert r['process_lock'] == 'runtime/runner.lock'
    assert 0 < r['max_wait_poll_seconds'] <= 5
    assert all(r[k] is False for k in ('capture_price', 'capture_funding', 'outcome_write', 'pnl_write', 'learning_write', 'knowledge_write', 'criterion_write', 'order_write', 'execution_write'))
    assert D['scheduler']['multiple_instances'] == 'IGNORE_NEW'
    assert D['scheduler']['start_when_available'] is True


def test_restart_and_continuity_are_fail_closed():
    assert D['restart_semantics'] == {
        'clock_regression': 'FAIL_CLOSED',
        'crash_after_attempt_start': 'PRESERVE_INCOMPLETE_OR_EXISTING_FINAL_STATE',
        'old_failed_retry': False, 'old_incomplete_completion': False, 'old_missed_capture': False,
        'resume_after_deadline': 'PRESERVE_ABSENCE_AND_MOVE_FORWARD',
        'resume_inside_current_open_window': 'ATTEMPT_ONLY_IF_NO_ATTEMPT_EXISTS',
    }
    assert D['continuity'] == {'states': ['SUCCESS', 'FAILED', 'MISSED_SLOT', 'INCOMPLETE', 'INVALID'], 'source': 'PERSISTED_VERIFIED_SLOT_ARTIFACTS', 'overwrite': False, 'invalid_terminal': True}
    assert D['readiness'] == {'name': 'METRICS_OPERATIONAL_READINESS_81H', 'required_consecutive_success_slots': 81, 'meaning': 'DATA_PLANE_READINESS_ONLY'}


def test_research_authority_is_unchanged_bytes():
    g = D['research_gate']
    assert g['name'] == 'FROZEN_OI_TAKER_RESEARCH_GATE_90D'
    assert g['authority'] == 'research/metrics_2024_2025/PROSPECTIVE_H1_PREREGISTRATION.json'
    assert g['sha256'] == PREREG_SHA
    assert hashlib.sha256((ROOT / g['authority']).read_bytes()).hexdigest() == PREREG_SHA
    assert g['redefined'] is g['evaluate_in_this_checkpoint'] is False
    assert g['uncaptured_interval'] == 'ABSENT_PROSPECTIVE_EVIDENCE'


def test_admission_is_design_only_and_requires_validator():
    a = D['observations_v2']
    assert a['status'] == 'DESIGNED_NOT_IMPLEMENTED'
    assert a['unsupported_metrics'] == 'UNKNOWN'
    assert a['whitelist_only_admission'] is a['derived'] is False
    assert a['dependencies'] == []
    assert set(a['required_checks']) == {'exact_contract_version', 'instrument_provider', 'exact_slot_source_period', 'complete_aligned_bundle', 'raw_hash_and_recomputed_values', 'causal_chronology', 'whole_capture_within_window', 'immutable_verified_SUCCESS', 'raw_no_dependencies', 'no_backfill', 'no_conflicting_observation', 'immutable_role'}
    assert D['scientific_status'] == {'EDGE': 'NOT_DEMONSTRATED', 'REGIME_VALIDATED': 'NO', 'MECHANICS_VALIDATED': 'NO', 'POLICY_WINNER': 'NONE'}


def test_protected_source_bytes_unchanged_at_design_freeze():
    # Qualification snapshot, not permission to modify these components.
    # Normalize checkout line endings only; preregistration above is byte-exact.
    for name, expected in PROTECTED_SOURCE_SHA256.items():
        assert hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected, name


PROTECTED_SOURCE_SHA256 = {
    'docs/FUNDING_H1_RUNTIME_DESIGN.json': 'f7557adaa63725466771c37d555d112a3ad027a3d6c5c2ad8da8f3d80ce11cdd',
    'core/market_mechanics/binance_live_adapter.py': '3d7c5ed0ee83b8e0354a6a1264b766df1a6ed467b6318c0553ed9bbee1108e5a',
    'core/scientific/prospective_receipts.py': '5b3a573bc9c90b848fe7a746cd2431f7704a130320ad609a2af442dfb2ae1a96',
    'core/scientific/price_continuity.py': '7758d84da7d09b411fa4425262fc38bc3921793de1576e20833bb47e34491f42',
    'scripts/capture_price_h1.py': 'b551eddb2d3265992ab7108b4062b3bc6fbc971219342076d7609104abc0d62a',
    'scripts/install_price_capture_task.ps1': '400e2992a800716855eae0b4445982c738a18f55f479db325ad359b7643abb12',
    'core/scientific/funding_h1_activation.py': 'ce88fc7634f55cf1a65a1550d6e2cd7cf6fddb5053df7c4c5e31a857e0757747',
    'core/scientific/funding_h1_runner.py': '04e489347638849f6dfaf007a555c3bcc261bf571a4fe3a57ed9ed40bc0fb61b',
    'core/scientific/funding_h1_live_adapter.py': 'b17f3b2787f64b3fe95440ba5fcfd1581ceb4ecfd8f8fa7d6829bf6f174b493c',
    'core/scientific/funding_h1_runtime.py': '2efa582586ec296736dd86c6d9493274317e28713ab89615ad42b4ca398b2a2a',
    'core/scientific/funding_continuity.py': 'a3ee940cf3687c5b13d68d6da1789989023bd71413d86ee090155660fa438044',
    'scripts/run_funding_h1.py': '7cbd045d83abec2ba4f2c06cdbcf519f7c41c63023a921a111b2d55e0a6e531f',
    'scripts/install_funding_h1_task.ps1': 'd9c394a86113cad2e5f5f7c4035f13f2daee008663248ef7b41f8a5634a61dc4',
    'scripts/activate_funding_h1.py': 'f6bec4bef40f73bce758b5a724fddb0b6b40af04b587e6fccd8b2d983108a2b8',
}
