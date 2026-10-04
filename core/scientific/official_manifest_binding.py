"""Create-once official declarations in one designated local custody directory."""
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
import json
import os

from .experimental_manifest import ExperimentalPopulationManifest, PopulationScope, ManifestState
from .nuisance_pilot_contracts import digest, utc


@dataclass(frozen=True, slots=True)
class OfficialManifestBinding:
    scope: PopulationScope
    manifest_id: str
    manifest_artifact_id: str
    manifest_content_digest: str
    frozen_at: datetime
    bound_at: datetime

    def __post_init__(self):
        if type(self.scope) is not PopulationScope:
            raise TypeError("exact population scope required")
        utc(self.frozen_at)
        utc(self.bound_at)
        if not self.scope.population_cutoff <= self.frozen_at <= self.bound_at:
            raise ValueError("cutoff <= frozen_at <= bound_at required")
        for value in (self.manifest_id, self.manifest_artifact_id, self.manifest_content_digest):
            if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("canonical SHA-256 commitment required")

    @property
    def scope_id(self):
        # Rules, protocol hash and cutoff are bound attributes, not escape hatches
        # for choosing another population in the same declared experiment.
        return digest(("pnep-official-scope-v1", self.scope.protocol_id,
                       self.scope.run_id, self.scope.dataset_role.value))

    @property
    def binding_id(self):
        # Retry time is not scientific identity; the first persisted time wins.
        return digest(("pnep-official-binding-v1", self.scope_id, self.scope.commitment(),
                       self.manifest_id, self.manifest_artifact_id, self.manifest_content_digest,
                       self.frozen_at.isoformat()))

    @property
    def artifact_id(self):
        return digest((self.binding_id, self.bound_at.isoformat()))

    def to_json(self):
        return json.dumps({"schema": "pnep-official-binding-v1", "scope": self.scope.commitment(),
            "scope_id": self.scope_id, "manifest_id": self.manifest_id,
            "manifest_artifact_id": self.manifest_artifact_id,
            "manifest_content_digest": self.manifest_content_digest,
            "frozen_at": self.frozen_at.isoformat(), "bound_at": self.bound_at.isoformat(),
            "binding_id": self.binding_id, "artifact_id": self.artifact_id},
            ensure_ascii=True, sort_keys=True, separators=(",", ":"))


class OfficialManifestStore:
    """One designated directory is the authority. No overwrite/delete/rebind API.

    A returned binding is official only after successful create or exact persisted
    verification. External custody must fix this directory and attest chronology.
    """
    def __init__(self, directory):
        self.__directory = Path(directory).resolve()
        self.__directory.mkdir(parents=True, exist_ok=True)

    def bind(self, scope, manifest, bound_at):
        if type(scope) is not PopulationScope:
            raise TypeError("exact population scope required")
        if type(manifest) is not ExperimentalPopulationManifest or manifest.state is not ManifestState.FROZEN:
            raise TypeError("exact FROZEN manifest required; no auto-freeze")
        if scope != manifest.scope:
            raise ValueError("scope/role mismatch")
        candidate = OfficialManifestBinding(scope, manifest.manifest_id, manifest.artifact_id,
            digest(manifest.to_json()), manifest.frozen_at, bound_at)
        path = self.__directory / (candidate.scope_id + ".json")
        payload = candidate.to_json() + "\n"
        try:
            stream = path.open("x", encoding="utf-8", newline="\n")
        except FileExistsError:
            # Interrupted writes, extra fields and noncanonical content fail
            # closed. No repair or truncation; preserve the conflicting artifact.
            try:
                existing = path.read_text(encoding="utf-8")
                data = json.loads(existing)
                first_time = datetime.fromisoformat(data["bound_at"])
                original = replace(candidate, bound_at=first_time)
                if original.to_json() + "\n" != existing:
                    raise ValueError("different official binding")
                if bound_at < first_time:
                    raise ValueError("retry predates original binding")
            except (ValueError, TypeError, KeyError):
                raise ValueError("OFFICIAL_BINDING_CONFLICT: existing artifact preserved") from None
            return original
        with stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return candidate
