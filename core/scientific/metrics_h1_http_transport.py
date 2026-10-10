"""One public Metrics GET, explicit injection only; never invoked at import.

Requests' timeout bounds connect/read waits, not total wall-clock duration.
The adapter/runner independently reject evidence outside the frozen deadline.
No retry, proxy inheritance, redirect, credentials, persistent session or cache.
"""
from math import isfinite

import requests

from core.market_mechanics.binance_live_adapter import BASE, METRIC_ENDPOINTS


def public_http_transport(url, *, params, timeout, allow_redirects=False):
    if type(url) is not str or url not in {BASE + p for p in METRIC_ENDPOINTS.values()}:
        raise ValueError('URL outside exact public Metrics whitelist')
    if (type(params) is not dict or params != {'symbol': 'BTCUSDT', 'period': '5m', 'limit': 5}
            or type(params.get('symbol')) is not str or type(params.get('period')) is not str
            or type(params.get('limit')) is not int):
        raise ValueError('exact Metrics parameters required')
    if type(timeout) not in (int, float) or not isfinite(timeout) or not 0 < timeout <= 8:
        raise ValueError('timeout must be finite numeric in (0,8]')
    if allow_redirects is not False:
        raise ValueError('redirects forbidden')
    with requests.Session() as session:
        session.trust_env = False
        session.headers.clear()
        session.headers.update({'Accept': 'application/json', 'Accept-Encoding': 'identity'})
        session.auth = None
        session.cert = None
        session.cookies.clear()
        session.proxies.clear()
        # Fresh Requests adapters have Retry(total=0, read=False). Do not install
        # retry middleware; fail closed if library defaults ever change.
        if any(a.max_retries.total != 0 for a in session.adapters.values()):
            raise ValueError('HTTP adapter retries forbidden')
        with session.get(url, params={'symbol': 'BTCUSDT', 'period': '5m', 'limit': 5},
                         timeout=timeout, allow_redirects=False, stream=False) as response:
            body = response.content
            if type(response.status_code) is not int or type(response.url) is not str or type(body) is not bytes:
                raise ValueError('malformed HTTP response')
            return response.status_code, response.url, body
