"""Synthetic firewall checks. Never print or publish policy performance."""
import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import pytest

from core.scientific import nuisance_pilot_contracts as c
from core.scientific import nuisance_pilot_store as s

T = datetime(2020, 1, 1, tzinfo=timezone.utc)


def outcome():
    return c.RestrictedOutcome(outcome_id="synthetic-outcome", opportunity_id="synthetic-opportunity",
        policy_id=c.PolicyID.P0, horizon_id="synthetic-horizon", protocol_hash="synthetic-protocol",
        policy_kernel_hash="synthetic-kernel", information_set_hash="synthetic-information",
        disposition=c.PolicyDisposition.POLICY_ENTER, direction=c.Direction.LONG,
        valuation_mode=c.ValuationMode.REFERENCE_EXPECTED, execution_scenario=c.ExecutionScenario.BASE,
        decision_at=T, outcome_window_start=T, outcome_window_end=T + timedelta(hours=1),
        computed_at=T, reason_codes=("SCHEMA_FIXTURE_ONLY",))


def safe():
    return c.SafeOutput(protocol_hash="0" * 64, release_id="1" * 64, generated_at=T,
        processor_code_hash="2" * 64, sealed_input_commitment="3" * 64, release_rule_hash="4" * 64)


def test_capabilities_are_enforced_and_errors_redacted():
    writer, reader = object(), object()
    store = s.RestrictedStore(writer_capability=writer, reader_capability=reader)
    record = outcome()
    assert store.append(record, capability=writer)
    assert not store.append(record, capability=writer)
    assert store.read(record.outcome_id, capability=reader) is record
    for wrong in (None, object(), writer):
        with pytest.raises(PermissionError):
            store.read(record.outcome_id, capability=wrong)
    with pytest.raises(PermissionError):
        store.append(record, capability=reader)
    with pytest.raises(s.ConflictError, match="^immutable identity conflict$"):
        store.append(replace(record, net_quote=Decimal("1")), capability=writer)
    assert repr(record) == "<RestrictedOutcome REDACTED>"


def test_restricted_lookup_errors_do_not_echo_identifiers():
    reader = object()
    store = s.RestrictedStore(writer_capability=object(), reader_capability=reader)
    with pytest.raises(KeyError, match="^'restricted record not found'$"):
        store.read("synthetic-private-identifier", capability=reader)
    with pytest.raises(TypeError, match="^immutable nonempty string identifiers required$"):
        store.read([], capability=reader)


def test_public_api_detached_and_cannot_query_outcomes():
    public = s.PublicSafeAPI(safe())
    assert {n for n in dir(public) if not n.startswith("_")} == {"release"}
    assert type(public.release()) is dict
    for name in ("read", "append", "list", "export", "query_policy", "query_event", "query_subgroup"):
        assert not hasattr(public, name)
    assert not hasattr(public, "__dict__")
    with pytest.raises(TypeError):
        s.PublicSafeAPI(outcome())
    with pytest.raises(TypeError):
        c.SafeOutput.from_mapping(outcome())
    with pytest.raises(TypeError):
        dict(outcome())


@pytest.mark.parametrize("field", ["extra", "metadata", "mean_effect", "effect_sign", "policy_pnl",
    "expectancy", "sharpe", "win_rate", "best_policy", "ranking", "paired_difference",
    "centered_residual", "localized_effect_ci", "pnl", "returns", "alpha", "performance", "effect"])
def test_safe_output_rejects_all_extra_fields_and_aliases(field):
    with pytest.raises(TypeError):
        c.SafeOutput.from_mapping({field: "synthetic-forbidden"})
    with pytest.raises(TypeError):
        replace(safe(), **{field: "synthetic-forbidden"})


def test_safe_output_identity_and_reason_fields_not_generic_metadata():
    with pytest.raises(ValueError):
        replace(safe(), reason_codes=("policy performance text",))
    with pytest.raises(ValueError):
        replace(safe(), protocol_hash={"hidden": "value"})
    with pytest.raises(ValueError):
        replace(safe(), pilot_state=c.PilotState.PARAMETER_READY)
    with pytest.raises(TypeError):
        replace(safe(), pilot_state="COLLECTING")


def test_restricted_role_access_and_unknown_values_fail_closed():
    record = outcome()
    with pytest.raises(ValueError):
        replace(record, dataset_role=c.DatasetRole.CONFIRMATION)
    with pytest.raises(ValueError):
        replace(record, access_class=c.AccessClass.SAFE_AGGREGATE)
    with pytest.raises(ValueError):
        replace(record, disposition=c.PolicyDisposition.INPUT_INELIGIBLE, net_quote=Decimal("0"))
    with pytest.raises(ValueError):
        replace(record, integrity_status=c.OutcomeIntegrity.VALID)
    with pytest.raises(TypeError):
        replace(record, net_quote=float("nan"))


def test_positive_synthetic_value_has_no_state_release_path():
    record = replace(outcome(), net_quote=Decimal("1"))
    run = c.PilotRun()
    with pytest.raises(TypeError):
        run.transition(c.PilotState.PARAMETER_READY, pnl=record.net_quote)
    with pytest.raises(ValueError):
        run.transition(c.PilotState.PARAMETER_READY)
    assert run.state is c.PilotState.NOT_STARTED
    with pytest.raises(TypeError):
        s.PublicSafeAPI(record)


def test_abstention_never_imputes_zero_and_cannot_have_exposure():
    abstain = replace(outcome(), disposition=c.PolicyDisposition.POLICY_ABSTAIN, direction=c.Direction.FLAT)
    assert abstain.net_quote is None
    with pytest.raises(ValueError):
        replace(abstain, net_quote=Decimal("1"))
    with pytest.raises(ValueError):
        replace(abstain, direction=c.Direction.LONG)
    with pytest.raises(ValueError):
        replace(abstain, integrity_status=c.OutcomeIntegrity.VALID, computed_at=T + timedelta(hours=1),
                record_hash="synthetic-record", outcome_receipt_ids=("synthetic-receipt",))


def test_import_and_call_surface_has_no_operational_connections():
    # AST allowlist stronger than looking for a few forbidden class names:
    # no dynamic imports, I/O, event bus, execution or operational modules.
    allowed = {"dataclasses", "datetime", "decimal", "enum", "hashlib", "json", "re", "nuisance_pilot_contracts"}
    forbidden = {"Council", "Criterion", "Knowledge", "OutcomeBridge", "PaperTradingEngine",
                 "OperationalLearningIntegrator", "publish", "emit", "update_capital", "exec", "eval",
                 "__import__", "open", "read_text", "read_bytes", "write_text", "write_bytes"}
    for module in (c, s):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name in allowed for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module in allowed
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                assert name not in forbidden
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                assert not any(isinstance(t, ast.Attribute) and "capital" in t.attr.lower() for t in targets)
