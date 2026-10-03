"""Outcome-blind population commitments. No sampling, outcome access or execution."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

from .nuisance_pilot_contracts import DatasetRole, EligibleDecisionOpportunity, closed, digest, identifiers, utc
from .common_support import CommonSupportRecord, CommonSupportRegistry, PolicyExclusion


class ManifestState(Enum):
    BUILDING = "BUILDING"
    FROZEN = "FROZEN"


@dataclass(frozen=True, slots=True)
class PopulationScope:
    protocol_id: str
    protocol_hash: str
    run_id: str
    dataset_role: DatasetRole
    population_rule_hash: str
    population_cutoff: datetime

    def __post_init__(self):
        identifiers((self.protocol_id, self.protocol_hash, self.run_id, self.population_rule_hash))
        if self.protocol_id != "OMA-PNEP-1.0":
            raise ValueError("unsupported protocol")
        closed(self.dataset_role, DatasetRole)
        utc(self.population_cutoff)

    def commitment(self):
        return (self.protocol_id, self.protocol_hash, self.run_id, self.dataset_role.value,
                self.population_rule_hash, self.population_cutoff.isoformat())


def _support_payload(record):
    return (record.opportunity_id, record.dataset_role.value, record.decision_at.isoformat(),
            record.comparison_id, record.controls_commitment, record.opportunity_commitment,
            tuple(p.value for p in record.eligible_policies),
            tuple((x.policy.value, tuple(r.value for r in x.reasons)) for x in record.exclusions),
            tuple((p.value, identity) for p, identity in record.decision_commitments), record.support_id)


@dataclass(frozen=True, slots=True)
class ExperimentalPopulationManifest:
    scope: PopulationScope
    records: tuple[CommonSupportRecord, ...]
    frozen_at: datetime

    def __post_init__(self):
        if type(self.scope) is not PopulationScope or type(self.records) is not tuple:
            raise TypeError("immutable scope and records required")
        utc(self.frozen_at)
        if self.frozen_at < self.scope.population_cutoff:
            raise ValueError("freeze precedes population cutoff")
        if any(type(r) is not CommonSupportRecord for r in self.records):
            raise TypeError("support records required")
        ids = tuple(r.opportunity_id for r in self.records)
        if len(set(ids)) != len(ids) or ids != tuple(sorted(ids)):
            raise ValueError("unique canonical opportunity order required")
        for record in self.records:
            if (type(record.eligible_policies) is not tuple or type(record.exclusions) is not tuple or
                    type(record.decision_commitments) is not tuple or
                    any(type(x) is not PolicyExclusion or type(x.reasons) is not tuple for x in record.exclusions) or
                    any(type(x) is not tuple for x in record.decision_commitments)):
                raise TypeError("immutable support snapshot required")
            if record.dataset_role is not self.scope.dataset_role or record.decision_at > self.scope.population_cutoff:
                raise ValueError("record outside population scope")

    @property
    def state(self):
        return ManifestState.FROZEN

    @property
    def manifest_id(self):
        # Materialization time is attestation metadata, not population identity.
        return digest(("pnep-population-v1", self.scope.commitment(),
                       tuple(_support_payload(r) for r in self.records)))

    @property
    def artifact_id(self):
        return digest((self.manifest_id, self.frozen_at.isoformat(), self.state.value))

    def to_json(self):
        return json.dumps({"schema": "pnep-population-v1", "scope": self.scope.commitment(),
            "records": tuple(_support_payload(r) for r in self.records),
            "frozen_at": self.frozen_at.isoformat(), "state": self.state.value,
            "manifest_id": self.manifest_id, "artifact_id": self.artifact_id},
            ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    def write_exclusive(self, path):
        """Export without overwriting. External custody/timestamping is required."""
        payload = self.to_json()
        with open(path, "x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload + "\n")


def _check_cutoff(record, cutoff):
    # Do not allow a post-cutoff receipt even to revise an exclusion reason.
    for value in (record.decision_at, record.assessed_at, record.source_event_time,
                  record.received_at, record.available_at, record.computed_at):
        if value is not None and value > cutoff:
            raise ValueError("post-cutoff evidence")
    for dependency in record.dependencies:
        _check_cutoff(dependency, cutoff)


class PopulationManifestBuilder:
    """One scope, one freeze. Call before outcome access; no external clock proof.

    No implicit support filtering: absent/ineligible and empty support are kept.
    Admission requires an existing support snapshot, never a silently filled one.
    """
    def __init__(self, scope):
        if type(scope) is not PopulationScope:
            raise TypeError("PopulationScope required")
        self.__scope = scope
        self.__registry = CommonSupportRegistry()
        self.__frozen = None

    @property
    def state(self):
        return ManifestState.FROZEN if self.__frozen is not None else ManifestState.BUILDING

    def add(self, opportunity, controls, decisions, support):
        if self.__frozen is not None:
            raise ValueError("FROZEN: population cannot change")
        if type(opportunity) is not EligibleDecisionOpportunity or type(support) is not CommonSupportRecord:
            raise TypeError("exact opportunity and existing support required")
        scope = self.__scope
        if (opportunity.protocol_id, opportunity.protocol_hash, opportunity.run_id,
                opportunity.dataset_role, opportunity.population_rule_hash) != (
                scope.protocol_id, scope.protocol_hash, scope.run_id, scope.dataset_role, scope.population_rule_hash):
            raise ValueError("population scope mismatch")
        if opportunity.decision_at > scope.population_cutoff:
            raise ValueError("opportunity after cutoff")
        if any(r.opportunity_id == opportunity.opportunity_id for r in self.__registry.records()):
            raise ValueError("duplicate opportunity")
        for record in opportunity.inputs:
            _check_cutoff(record, scope.population_cutoff)
        # Validate the existing snapshot against the same bounded evidence.
        # No newer inputs may replace it, and no absent policies are synthesized.
        verified = CommonSupportRegistry().register(opportunity, controls, decisions)
        if verified != support:
            raise ValueError("existing support commitment mismatch")
        self.__registry.register(opportunity, controls, decisions)

    def freeze(self, frozen_at):
        utc(frozen_at)
        if self.__frozen is not None:
            if frozen_at != self.__frozen.frozen_at:
                raise ValueError("FROZEN: freeze timestamp cannot change")
            return self.__frozen
        records = tuple(sorted(self.__registry.records(), key=lambda r: r.opportunity_id))
        manifest = ExperimentalPopulationManifest(self.__scope, records, frozen_at)
        self.__frozen = manifest
        return manifest
