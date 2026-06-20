"""O.M.A.-C.O.R.E. Data Quality Engine"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from core.schemas.event_schema import Event, AssetClass

class ValidationStatus(Enum):
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"

@dataclass
class ValidationResult:
    is_valid: bool
    status: ValidationStatus
    validation_score: float
    checks: Dict[str, bool]
    metadata: Dict[str, Any]
    warnings: List[str]
    errors: List[str]

class DataQualityEngine:
    """
    Motor de validación de calidad de datos para OMA-CORE.
    """
    
    VALIDATION_RULES = {
        AssetClass.CRYPTO: {
            "price_min": 0.00000001, "price_max": 1000000.0,
            "change_max": 50.0, "volume_min": 0, "age_max_hours": 2,
        },
        AssetClass.STOCK: {
            "price_min": 0.01, "price_max": 100000.0,
            "change_max": 20.0, "volume_min": 0, "age_max_hours": 4,
        },
        AssetClass.FOREX: {
            "price_min": 0.01, "price_max": 500.0,
            "change_max": 5.0, "volume_min": 0, "age_max_hours": 4,
        },
        AssetClass.COMMODITY: {
            "price_min": 0.01, "price_max": 10000.0,
            "change_max": 15.0, "volume_min": 0, "age_max_hours": 6,
        },
        AssetClass.INDEX: {
            "price_min": 0.01, "price_max": 100000.0,
            "change_max": 10.0, "volume_min": 0, "age_max_hours": 4,
        },
        AssetClass.BOND: {
            "price_min": 0.01, "price_max": 100.0,
            "change_max": 2.0, "volume_min": 0, "age_max_hours": 24,
        },
    }
    
    # Fuentes que pueden validarse entre sí (ahora incluye Binance)
    CROSS_VALIDATION_PAIRS = {
        "BTC": ["coingecko", "yahoo_finance", "binance"],
        "ETH": ["coingecko", "yahoo_finance", "binance"],
        "SOL": ["coingecko", "yahoo_finance", "binance"],
        "XRP": ["coingecko", "yahoo_finance", "binance"],
        "BNB": ["coingecko", "yahoo_finance", "binance"],
        "ADA": ["coingecko", "yahoo_finance", "binance"],
        "DOGE": ["coingecko", "yahoo_finance", "binance"],
        "AVAX": ["coingecko", "yahoo_finance", "binance"],
        "AAPL": ["yahoo_finance", "polygon"],
        "MSFT": ["yahoo_finance", "polygon"],
        "EURUSD": ["yahoo_finance", "forex"],
        "GC=F": ["yahoo_finance", "commodity"],
    }
    
    SOURCE_ACCURACY_HISTORY = {
        "coingecko": 0.95, "yahoo_finance": 0.95, "fred": 0.98,
        "binance": 0.96, "polymarket": 0.88,
        "rss_reuters_business": 0.90, "rss_bloomberg": 0.90,
        "rss_coindesk": 0.80, "rss_cointelegraph": 0.80, "rss_forexlive": 0.80,
        "rss_cnbc": 0.80, "rss_marketwatch": 0.80, "sentiment_fng_crypto": 0.85,
        "gdelt": 0.70, "osiris": 0.75,
    }

    def __init__(self, db=None):
        self.db = db

    def validate_event(self, event: Event) -> ValidationResult:
        checks = {}
        warnings = []
        errors = []

        checks["price_sane"] = self._check_price_sanity(event)
        if not checks["price_sane"]:
            errors.append("Precio fuera de rango válido")

        checks["change_sane"] = self._check_change_sanity(event)
        if not checks["change_sane"]:
            warnings.append("Cambio de precio extremo - verificar")

        checks["recent"] = self._check_recency(event)
        if not checks["recent"]:
            warnings.append(f"Datos antiguos (>{self._get_max_age(event)}h)")

        checks["source_reputable"] = self._check_source_reputation(event)
        if not checks["source_reputable"]:
            warnings.append("Fuente con baja reputación histórica")

        checks["cross_validated"] = self._cross_validate(event)
        if not checks["cross_validated"]:
            warnings.append("No se pudo validar cruzadamente")

        checks["internal_consistent"] = self._check_internal_consistency(event)
        if not checks["internal_consistent"]:
            errors.append("Inconsistencia interna en datos del evento")

        checks["not_duplicate"] = self._check_not_duplicate(event)
        if not checks["not_duplicate"]:
            warnings.append("Posible evento duplicado")

        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        validation_score = passed_checks / total_checks if total_checks > 0 else 0.0

        if errors:
            status = ValidationStatus.INVALID
            is_valid = False
        elif warnings and validation_score >= 0.7:
            status = ValidationStatus.WARNING
            is_valid = True
        elif validation_score >= 0.9:
            status = ValidationStatus.VALID
            is_valid = True
        else:
            status = ValidationStatus.UNCERTAIN
            is_valid = validation_score >= 0.5

        return ValidationResult(
            is_valid=is_valid, status=status, validation_score=round(validation_score, 3),
            checks=checks, metadata={
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "source": event.source, "event_type": event.event_type.value,
                "assets": [a.symbol for a in event.assets],
            },
            warnings=warnings, errors=errors
        )

    def validate_batch(self, events: List[Event]) -> Tuple[List[Event], List[Dict]]:
        valid_events = []
        rejected = []
        for event in events:
            result = self.validate_event(event)
            if result.is_valid:
                event.metadata["validation"] = {
                    "score": result.validation_score,
                    "status": result.status.value,
                    "checks": result.checks,
                }
                event.confidence = event.confidence * result.validation_score
                valid_events.append(event)
            else:
                rejected.append({
                    "event_id": event.id, "title": event.title,
                    "source": event.source, "reason": result.errors + result.warnings,
                    "validation_score": result.validation_score,
                })
        return valid_events, rejected

    def _check_price_sanity(self, event: Event) -> bool:
        if not event.assets:
            return True
        for asset in event.assets:
            if asset.price_at_event is None:
                continue
            rules = self.VALIDATION_RULES.get(asset.asset_class, self.VALIDATION_RULES[AssetClass.CRYPTO])
            if asset.price_at_event < rules["price_min"] or asset.price_at_event > rules["price_max"]:
                return False
        return True

    def _check_change_sanity(self, event: Event) -> bool:
        if "change_24h" not in event.metadata and "change_percent" not in event.metadata:
            return True
        change = event.metadata.get("change_24h") or event.metadata.get("change_percent", 0)
        if change is None:
            return True
        change = abs(float(change))
        if event.assets:
            rules = self.VALIDATION_RULES.get(event.assets[0].asset_class, self.VALIDATION_RULES[AssetClass.CRYPTO])
        else:
            rules = self.VALIDATION_RULES[AssetClass.CRYPTO]
        return change <= rules["change_max"]

    def _check_recency(self, event: Event) -> bool:
        age_hours = (datetime.now(timezone.utc) - event.timestamp).total_seconds() / 3600
        max_age = self._get_max_age(event)
        return age_hours <= max_age

    def _get_max_age(self, event: Event) -> int:
        if not event.assets:
            return 24
        rules = self.VALIDATION_RULES.get(event.assets[0].asset_class, self.VALIDATION_RULES[AssetClass.CRYPTO])
        return rules.get("age_max_hours", 24)

    def _check_source_reputation(self, event: Event) -> bool:
        accuracy = self.SOURCE_ACCURACY_HISTORY.get(event.source, 0.5)
        return accuracy >= 0.70

    def _cross_validate(self, event: Event) -> bool:
        if not self.db or not event.assets:
            return True
        symbol = event.assets[0].symbol
        if symbol not in self.CROSS_VALIDATION_PAIRS:
            return True
        try:
            recent_events = self.db.get_recent_events(hours=2, limit=50)
            cross_sources = self.CROSS_VALIDATION_PAIRS[symbol]
            for other_event in recent_events:
                if other_event.source in cross_sources and other_event.id != event.id:
                    if "change_24h" in event.metadata and "change_24h" in other_event.metadata:
                        e1_change = abs(float(event.metadata["change_24h"]))
                        e2_change = abs(float(other_event.metadata["change_24h"]))
                        if e2_change > 0 and abs(e1_change - e2_change) / e2_change > 0.5:
                            return False
            return True
        except Exception:
            return True

    def _check_internal_consistency(self, event: Event) -> bool:
        if event.sentiment_score > 0.3 and event.sentiment.value < 0:
            return False
        if event.sentiment_score < -0.3 and event.sentiment.value > 0:
            return False
        if event.event_type.value in ["hack_exploit", "geopolitical"] and event.urgency.value < 2:
            return False
        return True

    def _check_not_duplicate(self, event: Event) -> bool:
        if not self.db:
            return True
        try:
            recent = self.db.get_recent_events(hours=1, limit=100)
            for other in recent:
                if other.id != event.id and other.source == event.source:
                    if self._text_similarity(event.title, other.title) > 0.8:
                        return False
            return True
        except Exception:
            return True

    def _text_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0

    def get_source_accuracy(self, source: str) -> float:
        return self.SOURCE_ACCURACY_HISTORY.get(source, 0.5)

    def update_source_accuracy(self, source: str, was_correct: bool):
        current = self.SOURCE_ACCURACY_HISTORY.get(source, 0.5)
        alpha = 0.1
        new_accuracy = current + alpha * (1.0 if was_correct else 0.0 - current)
        self.SOURCE_ACCURACY_HISTORY[source] = round(new_accuracy, 3)
