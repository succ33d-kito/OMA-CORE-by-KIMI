"""Semantically conservative projection from causal observations to LatentMarketContext.

STEP 49A.2.

Only exact compatible meanings are projected. Levels are never converted into
changes, ratios are never silently converted into imbalances, and missing or
unsupported features remain explicit.
"""

from dataclasses import dataclass, field
from math import isfinite
import json

from core.market_mechanics.latent_context import (
    LatentMarketContext,
    TimedValue,
    build_latent_context,
)

from .causal_observation_snapshot import (
    CausalObservationSnapshot,
)

from .prospective_receipts import (
    observation_hash,
)


DIRECT_MAPPINGS = {
    "FundingRate/Published": (
        "funding_rate",
        "funding_rate",
    ),
    "MarketMetrics/GlobalPositioning": (
        "long_short_ratio",
        "value",
    ),
}


def _number(value, *, feature):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"invalid numeric payload for {feature}"
        ) from None

    if not isfinite(number):
        raise ValueError(
            f"non-finite numeric payload for {feature}"
        )

    return number


@dataclass(frozen=True, slots=True)
class LatentContextProjection:
    snapshot_id: str
    instrument: str
    as_of: object
    context: LatentMarketContext
    used_observation_ids: tuple[str, ...]
    unconsumed_features: tuple[str, ...]
    projection_id: str = field(init=False)

    def __post_init__(self):
        if not self.snapshot_id or not self.instrument:
            raise ValueError(
                "snapshot and instrument required"
            )

        if type(self.context) is not LatentMarketContext:
            raise TypeError(
                "LatentMarketContext required"
            )

        if type(self.used_observation_ids) is not tuple:
            raise TypeError(
                "immutable used-observation tuple required"
            )

        if (
            len(set(self.used_observation_ids))
            != len(self.used_observation_ids)
        ):
            raise ValueError(
                "duplicate used observation"
            )

        if type(self.unconsumed_features) is not tuple:
            raise TypeError(
                "immutable unconsumed-feature tuple required"
            )

        payload = {
            "schema":
                "causal-latent-context-projection-v1",
            "snapshot_id":
                self.snapshot_id,
            "instrument":
                self.instrument,
            "as_of":
                self.as_of.isoformat(),
            "context":
                self.context.to_dict(),
            "used_observation_ids":
                list(self.used_observation_ids),
            "unconsumed_features":
                list(self.unconsumed_features),
        }

        object.__setattr__(
            self,
            "projection_id",
            observation_hash(payload),
        )

    def to_dict(self):
        return {
            "schema":
                "causal-latent-context-projection-v1",
            "projection_id":
                self.projection_id,
            "snapshot_id":
                self.snapshot_id,
            "instrument":
                self.instrument,
            "as_of":
                self.as_of.isoformat(),
            "context":
                self.context.to_dict(),
            "used_observation_ids":
                list(self.used_observation_ids),
            "unconsumed_features":
                list(self.unconsumed_features),
        }


def project_latent_context(snapshot):
    """Project only semantically exact observations into existing context."""

    if type(snapshot) is not CausalObservationSnapshot:
        raise TypeError(
            "CausalObservationSnapshot required"
        )

    kwargs = {}
    used = []
    consumed_features = set()

    for observation in snapshot.observations:
        mapping = DIRECT_MAPPINGS.get(
            observation.feature
        )

        if mapping is None:
            continue

        axis, payload_field = mapping

        payload = json.loads(
            observation.payload_json
        )

        if payload_field not in payload:
            raise ValueError(
                f"required payload field missing "
                f"for {observation.feature}"
            )

        value = _number(
            payload[payload_field],
            feature=observation.feature,
        )

        kwargs[axis] = TimedValue(
            observed_at=observation.source_metric_at,
            value=value,
            source=(
                "observations_v2:"
                + observation.id
            ),
        )

        used.append(
            observation.id
        )

        consumed_features.add(
            observation.feature
        )

    context = build_latent_context(
        as_of=snapshot.as_of,
        **kwargs,
    )

    unconsumed = tuple(
        observation.feature
        for observation in snapshot.observations
        if observation.feature
        not in consumed_features
    )

    return LatentContextProjection(
        snapshot_id=snapshot.snapshot_id,
        instrument=snapshot.instrument,
        as_of=snapshot.as_of,
        context=context,
        used_observation_ids=tuple(used),
        unconsumed_features=unconsumed,
    )