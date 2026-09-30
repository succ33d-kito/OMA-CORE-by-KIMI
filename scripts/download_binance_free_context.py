#!/usr/bin/env python3
"""Print/download plan for zero-cost Binance public context archives.
Network transfer is intentionally separate from parsing so research remains reproducible.
"""
from argparse import ArgumentParser
from datetime import date,timedelta
BASE="https://data.binance.vision/data/futures/um"
def urls(symbol,start,end):
 d=start
 while d<=end:
  stem=f"{BASE}/daily/metrics/{symbol}/{symbol}-metrics-{d.isoformat()}.zip"
  yield stem; yield stem+".CHECKSUM"; d+=timedelta(days=1)
if __name__=="__main__":
 p=ArgumentParser(); p.add_argument("--symbol",default="BTCUSDT"); p.add_argument("--start",required=True); p.add_argument("--end",required=True)
 a=p.parse_args(); s=date.fromisoformat(a.start); e=date.fromisoformat(a.end)
 if e<s: raise SystemExit("end before start")
 print("\n".join(urls(a.symbol,s,e)))
