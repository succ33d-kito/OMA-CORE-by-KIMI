"""One price-only prospective probe. No outcomes, scheduling or holdout access."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.market_mechanics.binance_live_adapter import capture_price_receipt
from core.scientific.prospective_receipts import is_causally_available, load_observations


def run(ledger, report):
    import requests
    if report.exists():
        raise FileExistsError('Preserve existing probe evidence; choose a new report path')
    result = {'status':'ENGINEERING VERIFIED / LIVE NOT VERIFIED',
              'historical_2024':'UNPROVEN','MM_READY':0,'MM_BLOCKED':10,
              'holdouts_opened':False,'edge':False,'promotion':'NONE'}
    try:
        with requests.Session() as session:
            receipt = capture_price_receipt(session, ledger)
        decision = datetime.now(timezone.utc)  # Independent of source event time.
        if not is_causally_available(ledger, receipt['id'], decision):
            raise ValueError('persisted observation failed Point-in-Time gate')
        replay = load_observations(ledger)[receipt['id']]
        if replay != receipt:
            raise ValueError('replay changed provenance')
        received = datetime.fromisoformat(receipt['received_at'])
        close = datetime.fromisoformat(receipt['source_metric_at'])
        result.update(status='PROSPECTIVE_CAUSAL_AVAILABILITY_VERIFIED',
                      evidence_scope='This observation only, under trusted host UTC clock and TLS capture; no continuous coverage claim',
                      observation=receipt, decision_at=decision.isoformat(),
                      latency_seconds_samples=[(received-close).total_seconds()],
                      latency_scope='REST polling delay plus transport; not intrinsic exchange publication latency',
                      valid_from=receipt['available_at'])
    except (requests.RequestException, ValueError, RuntimeError, OSError, TypeError, KeyError, IndexError) as error:
        result['technical_blocker']=f'{type(error).__name__}: {error}'
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k!='observation'},indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger',type=Path,required=True,help='Existing prospective receipt DB; v2 table shares it with legacy receipts')
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();r=run(a.ledger,a.report)
    raise SystemExit(0 if r['status']=='PROSPECTIVE_CAUSAL_AVAILABILITY_VERIFIED' else 2)
