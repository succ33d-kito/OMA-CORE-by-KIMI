"""Append-only binary forecasts and explicit labels; no auto-learning."""
from datetime import datetime, timezone
import json
from math import isfinite, log
import sqlite3


def _time(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone required")
    return value.astimezone(timezone.utc).isoformat()


class ForecastJournal:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS forecasts (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS forecast_labels (id TEXT PRIMARY KEY REFERENCES forecasts(id), payload TEXT NOT NULL)")

    def record(self, *, forecast_id, target, probability, issued_at, horizon_end,
               available_at, model_version, regime_id=None, context=None, regime_label=None):
        issued, end, available = map(_time, (issued_at, horizon_end, available_at))
        if not forecast_id or not target or not model_version:
            raise ValueError("forecast id, precise target and model version required")
        if isinstance(probability, bool) or not isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("probability must be finite and in [0,1]")
        if not available <= issued < end:
            raise ValueError("invalid forecast information/horizon times")
        payload = json.dumps(dict(target=target, probability=probability, issued_at=issued,
                                  horizon_end=end, available_at=available, model_version=model_version,
                                  regime_id=regime_id, regime_label=regime_label, context=context or {}), sort_keys=True)
        with sqlite3.connect(self.path) as db:
            old = db.execute("SELECT payload FROM forecasts WHERE id=?", (forecast_id,)).fetchone()
            if old and old[0] != payload:
                raise ValueError("forecast is immutable")
            db.execute("INSERT OR IGNORE INTO forecasts VALUES (?,?)", (forecast_id, payload))

    def resolve(self, forecast_id, *, outcome, observed_at, source_id):
        if type(outcome) is not bool or not source_id:
            raise ValueError("binary outcome and label provenance required")
        observed = _time(observed_at)
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA foreign_keys=ON")
            row = db.execute("SELECT payload FROM forecasts WHERE id=?", (forecast_id,)).fetchone()
            if not row or observed < json.loads(row[0])["horizon_end"]:
                raise ValueError("forecast missing or outcome horizon incomplete")
            payload = json.dumps(dict(outcome=outcome, observed_at=observed, source_id=source_id), sort_keys=True)
            old = db.execute("SELECT payload FROM forecast_labels WHERE id=?", (forecast_id,)).fetchone()
            if old and old[0] != payload:
                raise ValueError("label is immutable")
            db.execute("INSERT OR IGNORE INTO forecast_labels VALUES (?,?)", (forecast_id, payload))

    def forecasts(self, pending_only=False):
        with sqlite3.connect(self.path) as db:
            query = "SELECT f.id, f.payload FROM forecasts f"
            if pending_only:
                query += " WHERE NOT EXISTS (SELECT 1 FROM forecast_labels l WHERE l.id=f.id)"
            rows = db.execute(query).fetchall()
        return {key: json.loads(payload) for key, payload in rows}

    def get(self, forecast_id):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM forecasts WHERE id=?", (forecast_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def evaluate(self, *, target, model_version, regime_id=None, regime_label=None, bins=10):
        if type(bins) is not int or bins < 1:
            raise ValueError("positive integer bins required")
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT f.payload, l.payload FROM forecasts f JOIN forecast_labels l ON f.id=l.id").fetchall()
        pairs = []
        for raw_f, raw_l in rows:
            f, label = json.loads(raw_f), json.loads(raw_l)
            if f["target"] == target and f["model_version"] == model_version and (regime_id is None or f["regime_id"] == regime_id) and (regime_label is None or f.get("regime_label") == regime_label):
                pairs.append((f["probability"], int(label["outcome"])))
        reliability = []
        for i in range(bins):
            bucket = [(p,y) for p,y in pairs if min(int(p*bins), bins-1) == i]
            reliability.append(dict(lower=i/bins, upper=(i+1)/bins, count=len(bucket),
                                    mean_probability=sum(p for p,y in bucket)/len(bucket) if bucket else None,
                                    observed_frequency=sum(y for p,y in bucket)/len(bucket) if bucket else None))
        n = len(pairs)
        clipped = [(min(1-1e-15,max(1e-15,p)),y) for p,y in pairs]
        return dict(target=target, model_version=model_version, count=n,
                    brier=sum((p-y)**2 for p,y in pairs)/n if n else None,
                    log_loss=-sum(y*log(p)+(1-y)*log(1-p) for p,y in clipped)/n if n else None,
                    log_loss_clip=1e-15,
                    expected_calibration_error=sum(b["count"]*abs(b["mean_probability"]-b["observed_frequency"])
                                                   for b in reliability if b["count"])/n if n else None,
                    reliability=reliability, status="descriptive_only" if n else "no_resolved_forecasts")
