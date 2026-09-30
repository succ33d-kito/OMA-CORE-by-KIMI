"""Download the prespecified BTCUSDT spot hourly 2025 research dataset."""

from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

import requests


def download_month(month):
    name = f"BTCUSDT-1h-2025-{month:02d}.zip"
    url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/{name}"
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    checksum = requests.get(url + ".CHECKSUM", timeout=45)
    checksum.raise_for_status()
    expected = checksum.text.split()[0].lower()
    actual = sha256(response.content).hexdigest()
    if expected != actual:
        raise ValueError(f"checksum mismatch: {name}")
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        raw = archive.read(name.replace(".zip", ".csv")).decode()
    bars = []
    for row in csv.reader(io.StringIO(raw)):
        # Spot archive timestamps from January 2025 are microseconds.
        timestamp = datetime.fromtimestamp(int(row[0]) / 1_000_000, tz=timezone.utc)
        if timestamp.year != 2025 or timestamp.month != month:
            raise ValueError(f"unexpected timestamp: {name}")
        bars.append(dict(time=timestamp.isoformat(), **{
            key: float(row[i+1]) for i, key in enumerate(("open", "high", "low", "close", "volume"))
        }))
    return bars, {"url": url, "sha256": actual, "checksum_verified": True,
                  "rows": len(bars), "retrieved_at": datetime.now(timezone.utc).isoformat()}


def main():
    directory = Path(__file__).resolve().parents[1] / "research" / "data"
    directory.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(download_month, range(1, 13)))
    bars = [bar for data, _ in results for bar in data]
    encoded = json.dumps(bars, indent=2).encode()
    (directory / "BTCUSDT_1h_2025.json").write_bytes(encoded)
    manifest = {"symbol": "BTCUSDT", "market": "spot", "year": 2025,
                "timeframe": "1h", "bars": len(bars), "json_sha256": sha256(encoded).hexdigest(),
                "archives": [metadata for _, metadata in results]}
    (directory / "BTCUSDT_1h_2025_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"bars": len(bars), "verified_archives": len(results),
                      "first": bars[0]["time"], "last": bars[-1]["time"]}))


if __name__ == "__main__":
    main()
