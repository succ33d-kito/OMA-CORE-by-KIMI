"""Execution evidence only. No capture, estimates, fills, payments or total cost."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from enum import Enum
import json

from .nuisance_pilot_contracts import DatasetRole, InputStatus, closed, digest, identifiers, utc
from .policy_kernel import canonical


class EvidenceKind(Enum):
    BOOK = "https://fapi.binance.com/fapi/v1/ticker/bookTicker"
    MARK_FUNDING = "https://fapi.binance.com/fapi/v1/premiumIndex"
    USER_FEES = "https://fapi.binance.com/fapi/v1/commissionRate"


class Measure(Enum):
    BID_USDT_PER_BTC = "bidPrice"
    ASK_USDT_PER_BTC = "askPrice"
    MARK_USDT_PER_BTC = "markPrice"
    INDEX_USDT_PER_BTC = "indexPrice"
    LATEST_FUNDING_RATE_FRACTION = "lastFundingRate"
    MAKER_FEE_RATE_FRACTION = "makerCommissionRate"
    TAKER_FEE_RATE_FRACTION = "takerCommissionRate"


def _kind(measure):
    closed(measure, Measure)
    if measure in (Measure.BID_USDT_PER_BTC, Measure.ASK_USDT_PER_BTC):
        return EvidenceKind.BOOK
    if measure in (Measure.MAKER_FEE_RATE_FRACTION, Measure.TAKER_FEE_RATE_FRACTION):
        return EvidenceKind.USER_FEES
    return EvidenceKind.MARK_FUNDING


def _pairs(items):
    if len({k for k, _ in items}) != len(items):
        raise ValueError("duplicate response field")
    return dict(items)


def _decimal(value):
    if type(value) is not str or len(value) > 80:
        raise TypeError("provider decimal string required; no bps/percent conversion")
    result = Decimal(value)
    if not result.is_finite() or len(result.as_tuple().digits) > 38 or abs(result.as_tuple().exponent) > 18:
        raise ValueError("unsupported nonfinite or excessive decimal precision")
    return result


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    """Upstream capture reference, NOT self-authenticating proof of HTTP reception.

    Only source response fields are interpreted. Receipt identity, timestamps and
    provenance must be attested by a future trusted capture adapter.
    """
    kind: EvidenceKind
    source: str
    receipt_id: str
    provenance_sha256: str
    response_json: str
    dataset_role: DatasetRole
    request_started_at: datetime | None
    received_at: datetime | None
    available_at: datetime | None
    fee_account_reference: str | None

    def __post_init__(self):
        closed(self.kind, EvidenceKind)
        closed(self.dataset_role, DatasetRole)
        identifiers((self.source, self.receipt_id, self.provenance_sha256))
        if self.source != self.kind.value:
            raise ValueError("wrong execution evidence source")
        if len(self.provenance_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.provenance_sha256):
            raise ValueError("capture provenance commitment required")
        if type(self.response_json) is not str:
            raise TypeError("immutable raw response string required")
        if self.kind is EvidenceKind.USER_FEES:
            identifiers((self.fee_account_reference,))
        elif self.fee_account_reference is not None:
            raise ValueError("account reference only belongs to fee evidence")
        for at in (self.request_started_at, self.received_at, self.available_at):
            if at is not None:
                utc(at)
        if self.request_started_at is not None and self.received_at is not None and self.request_started_at > self.received_at:
            raise ValueError("request after receipt")
        if self.received_at is not None and self.available_at is not None and self.received_at > self.available_at:
            raise ValueError("availability before receipt")
        payload = self.payload()
        exchange = payload.get("time")
        if exchange is not None and self.received_at is not None and self.exchange_at > self.received_at:
            raise ValueError("exchange timestamp after receipt")

    def payload(self):
        data = json.loads(self.response_json, object_pairs_hook=_pairs)
        extras = {
            EvidenceKind.BOOK: {"bidQty", "askQty", "time"},
            EvidenceKind.MARK_FUNDING: {"estimatedSettlePrice", "interestRate", "nextFundingTime", "time"},
            EvidenceKind.USER_FEES: {"rpiCommissionRate"},
        }[self.kind]
        allowed = {"symbol"} | extras | {m.value for m in Measure if _kind(m) is self.kind}
        if type(data) is not dict or set(data) - allowed or data.get("symbol") != "BTCUSDT":
            raise ValueError("wrong symbol or unsupported response fields")
        for key, value in tuple(data.items()):
            if key == "symbol" or value is None:
                continue
            if key in ("time", "nextFundingTime"):
                if type(value) is not int or value < 0:
                    raise ValueError("timestamp must be integer epoch milliseconds")
            else:
                data[key] = _decimal(value)
                if "Price" in key and data[key] <= 0:
                    raise ValueError("positive observed price required")
                if key.endswith("Qty") and data[key] < 0:
                    raise ValueError("negative quantity")
                if "Rate" in key and data[key].copy_abs() > 1:
                    raise ValueError("rate is a decimal fraction, never percent or bps")
        bid, ask = data.get("bidPrice"), data.get("askPrice")
        if bid is not None and ask is not None and bid > ask:
            raise ValueError("crossed book: bid exceeds ask")
        return data

    @property
    def exchange_at(self):
        value = self.payload().get("time")
        return None if value is None else datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=value)

    @property
    def identity(self):
        return digest(("execution-receipt-v1", self.kind.value, self.source, self.receipt_id,
            self.provenance_sha256, tuple((k, canonical(v)) for k, v in sorted(self.payload().items())),
            self.dataset_role.value, *(x.isoformat() if x is not None else None for x in
            (self.request_started_at, self.received_at, self.available_at)), self.fee_account_reference))

    def status_at(self, decision_at):
        utc(decision_at)
        if self.received_at is None or self.available_at is None:
            return InputStatus.UNKNOWN
        return InputStatus.LATE if self.available_at > decision_at else InputStatus.VALID


@dataclass(frozen=True, slots=True)
class ExecutionObservation:
    instrument: str
    venue: str
    product: str
    dataset_role: DatasetRole
    decision_at: datetime
    receipts: tuple[ExecutionReceipt, ...]

    def __post_init__(self):
        if (self.instrument, self.venue, self.product) != ("BTCUSDT", "Binance USDⓈ-M", "linear perpetual"):
            raise ValueError("unsupported execution universe")
        closed(self.dataset_role, DatasetRole)
        utc(self.decision_at)
        if type(self.receipts) is not tuple or any(type(r) is not ExecutionReceipt for r in self.receipts):
            raise TypeError("immutable execution receipts required")
        if len({r.kind for r in self.receipts}) != len(self.receipts) or len({r.receipt_id for r in self.receipts}) != len(self.receipts):
            raise ValueError("duplicate evidence kind or receipt identity")
        if any(r.dataset_role is not self.dataset_role for r in self.receipts):
            raise ValueError("cross-role execution evidence")

    def status(self, measure):
        kind = _kind(measure)
        receipt = next((r for r in self.receipts if r.kind is kind), None)
        if receipt is None or receipt.payload().get(measure.value) is None:
            return InputStatus.UNKNOWN
        return receipt.status_at(self.decision_at)

    def value(self, measure):
        if self.status(measure) is not InputStatus.VALID:
            return None
        return next(r for r in self.receipts if r.kind is _kind(measure)).payload()[measure.value]

    def _book_derived(self, mid):
        bid, ask = self.value(Measure.BID_USDT_PER_BTC), self.value(Measure.ASK_USDT_PER_BTC)
        if bid is None or ask is None:
            return None
        # Bounded input precision and fixed local context prevent global Decimal
        # settings from changing the result. Both quotes come from one receipt.
        with localcontext() as context:
            context.prec = 100
            return (bid + ask) / Decimal(2) if mid else ask - bid

    @property
    def mid_usdt_per_btc(self):
        return self._book_derived(True)

    @property
    def spread_usdt_per_btc(self):
        return self._book_derived(False)

    @property
    def slippage(self):
        return None  # NOT_OBSERVED; this contract has no execution or estimate.

    @property
    def observation_id(self):
        return digest(("execution-observation-v1", self.instrument, self.venue, self.product,
            self.dataset_role.value, self.decision_at.isoformat(),
            tuple(sorted(r.identity for r in self.receipts))))
