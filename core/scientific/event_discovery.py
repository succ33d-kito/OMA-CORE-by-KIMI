"""SEC-only prospective discovery. No semantic classification or outcome access.

Local append-only custody and OS locks, not protection against hostile Python.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
import hashlib
import os
import sys
import time
import xml.etree.ElementTree as ET

from . import real_event_receipt as events
from .nuisance_pilot_contracts import DatasetRole
from .event_direction_operator import _open

def digest(value):
    return hashlib.sha256(events._json(value).encode('utf-8')).hexdigest()


SCHEMA = 'sec-document-discovery-v1'
ENDPOINT = 'https://www.sec.gov/news/pressreleases.rss'
SCOPE = 'SEC_OFFICIAL_PRESS_RELEASES_RSS_V1'
USER_AGENT = 'OMA-CORE/51-Event-Discovery-v1 (prospective research; https://github.com/succ33d-kito/OMA-CORE-by-KIMI)'
INTERVAL = 300
MAX_BYTES = 4 * 1024 * 1024
CONTRACT = dict(schema=SCHEMA, scope=SCOPE, role='PILOT', endpoint=ENDPOINT,
    hosts=['www.sec.gov'], document_prefix='/newsroom/press-releases/',
    parser='rss2-stdlib-strict-v1', polling='one-shot-300s-no-invocation-retry-v1',
    interval_seconds=INTERVAL, baseline='exclude-guid-or-link-forever',
    revisions='recheck-visible-prospective-documents-on-normal-poll',
    redirects='reject-all', user_agent=USER_AGENT)
CONTRACT_HASH = digest(CONTRACT)

# --- Additive contract revision V2 (append-only supersession; V1 stays frozen) ---
# The ONLY behavioural difference is the User-Agent: the proven SEC HTTP 403 was
# caused by a User-Agent without contact information. The contact below is frozen
# with explicit owner authorisation and must not be altered without a new revision.
SUPERSESSION_KIND = 'authority_supersession'
REVISION_REASON = 'SEC_HTTP_403_CONTACT_USER_AGENT'
CONTACT_APPROVED = 'mazonmalda@gmail.com'
USER_AGENT_V2 = ('OMA-CORE/51-Event-Discovery-v1 (prospective research; '
                 'contact: ' + CONTACT_APPROVED + ')')
CONTRACT_V2 = dict(CONTRACT, user_agent=USER_AGENT_V2)
CONTRACT_V2_HASH = digest(CONTRACT_V2)
CONTRACT_CHAIN = {CONTRACT_HASH: CONTRACT, CONTRACT_V2_HASH: CONTRACT_V2}
_HEX = '0123456789abcdef'


def supersession_record(*, previous_authority_id, previous_contract_hash,
                        contract=CONTRACT_V2, reason=REVISION_REASON):
    """Build (never write) an append-only revision record for an activated authority.

    The superseding authorisation continues the SAME logical source and the SAME
    journal. It cannot rebaseline, renumber or reinterpret history.
    """
    if type(contract) is not dict or contract not in CONTRACT_CHAIN.values() \
            or digest(contract) not in CONTRACT_CHAIN:
        raise ValueError('unknown contract revision')
    for value in (previous_authority_id, previous_contract_hash):
        if type(value) is not str or len(value) != 64 or any(c not in _HEX for c in value):
            raise ValueError('hex digest required')
    if type(reason) is not str or not reason.strip() or reason != reason.strip():
        raise ValueError('explicit revision reason required')
    return dict(previous_authority_id=previous_authority_id,
                previous_contract_hash=previous_contract_hash,
                supersedes_authority_id=previous_authority_id,
                contract=contract, contract_hash=digest(contract), reason=reason)


def _guard(*paths):
    if 'pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST'):
        if any('prospective' in [s.lower() for s in Path(p).resolve().parts] for p in paths):
            raise ValueError('test process cannot access production prospective state')


def _url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'www.sec.gov' or p.query or p.fragment
            or not p.path.startswith('/newsroom/press-releases/')
            or not p.path.removeprefix('/newsroom/press-releases/')
            or any(x in p.path for x in ('%', '\\', '//', '/./', '/../'))):
        raise ValueError('INVALID_SCOPE')
    return url


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('INVALID_SCOPE: redirect rejected')


def _fetch(url, *, feed, user_agent=None):
    """One bounded HTTP request; no retries and no redirects, even within host."""
    if not feed:
        time.sleep(1)  # At most one document request per second; no parallel fetches.
    agent = USER_AGENT if user_agent is None else user_agent
    if type(agent) is not str or not agent.strip():
        raise ValueError('explicit user agent required')
    with build_opener(_NoRedirect()).open(Request(url, headers={
            'User-Agent': agent, 'Accept-Encoding': 'identity'}), timeout=20) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError('INVALID_SCOPE: response identity')
        kind = response.headers.get_content_type()
        allowed = ('application/rss+xml', 'application/xml', 'text/xml') if feed else ('text/html', 'text/plain')
        if kind not in allowed:
            raise ValueError('INVALID_FEED' if feed else 'INVALID_DOCUMENT')
        raw = response.read(MAX_BYTES + 1)
        received = events._now()
        length = response.headers.get('Content-Length')
        if not raw or len(raw) > MAX_BYTES or (length is not None and int(length) != len(raw)):
            raise ValueError('INVALID_FEED' if feed else 'INVALID_DOCUMENT')
        raw.decode('utf-8', errors='strict')
        return raw, received, kind


def _parse(raw):
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('INVALID_FEED: entities forbidden')
    root = ET.fromstring(raw)
    if root.tag != 'rss' or root.get('version') != '2.0' or len(root.findall('channel')) != 1:
        raise ValueError('INVALID_FEED')
    channel = root.find('channel')
    if (channel.findtext('title') or '').strip() != 'Press Releases':
        raise ValueError('INVALID_FEED: channel')
    items = []
    for node in channel.findall('item'):
        if any(len(node.findall(k)) > 1 for k in ('link', 'guid', 'title', 'pubDate')):
            raise ValueError('INVALID_FEED: duplicate fields')
        link = _url((node.findtext('link') or '').strip())
        guid = (node.findtext('guid') or '').strip()
        item = dict(link=link, guid=guid, title=(node.findtext('title') or '').strip(),
                    published_at=node.findtext('pubDate'), raw_item=ET.tostring(node, encoding='unicode'))
        item['item_id'] = digest((SCOPE, guid or link))
        item['metadata_hash'] = digest(item)
        if any(i['item_id'] == item['item_id'] or i['link'] == link for i in items):
            raise ValueError('INVALID_FEED: duplicate identity')
        items.append(item)
    # An empty response must not establish a false empty baseline.
    if not items:
        raise ValueError('INVALID_FEED: empty channel')
    return items


@contextmanager
def _lock(root):
    # Persistent lock file; locks are released by the OS after a crash.
    with (Path(root) / 'poll.lock').open('a+b') as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == 'win32':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class SourceDiscoveryAuthorityV1:
    def __init__(self, root):
        self.root = Path(root).resolve()
        _guard(self.root)
        self.path = self.root / 'discovery.sqlite'
        self.journal = events.RealEventStore(self.path, read_only=True)
        rows = self.journal._rows()
        if not rows or rows[0]['kind'] != 'discovery_authority':
            raise ValueError('discovery activation missing')
        self.activation = rows[0]
        config = self.activation['data']
        activation_contract = config['contract']
        if (type(activation_contract) is not dict or activation_contract not in CONTRACT_CHAIN.values()
                or digest(activation_contract) not in CONTRACT_CHAIN
                or config['contract_hash'] != digest(activation_contract)):
            raise ValueError('discovery contract mismatch')
        self.authority_id = digest(self.activation)
        # Append-only contract revisions: the activation authority stays immutable and
        # auditable; each revision must chain from the authority it supersedes.
        self.authority_ids = [self.authority_id]
        self.supersessions = []
        active_authority_id, active_contract_hash = self.authority_id, config['contract_hash']
        active_contract = activation_contract
        for row in rows:
            if row['kind'] != SUPERSESSION_KIND:
                continue
            data = row['data']
            new_contract = data.get('contract')
            if (data.get('previous_authority_id') != active_authority_id
                    or data.get('previous_contract_hash') != active_contract_hash
                    or data.get('supersedes_authority_id') != active_authority_id
                    or type(new_contract) is not dict or new_contract not in CONTRACT_CHAIN.values()
                    or digest(new_contract) not in CONTRACT_CHAIN
                    or data.get('contract_hash') != digest(new_contract)):
                raise ValueError('supersession chain mismatch')
            active_authority_id = digest(row)
            active_contract_hash, active_contract = digest(new_contract), new_contract
            self.authority_ids.append(active_authority_id)
            self.supersessions.append(row)
        self.active_authority_id = active_authority_id
        self.active_contract_hash = active_contract_hash
        self.active_contract = active_contract
        self.source_path = Path(config['source_path'])
        _guard(self.source_path, config['operator_root'])
        _, authority, _, _, binding = _open(config['operator_root'], DatasetRole.PILOT)
        if (authority.authority_id != config['direction_authority_id'] or digest(binding) != config['operator_binding']
                or Path(binding['data']['event_journal']).resolve() != self.source_path
                or datetime.fromisoformat(binding['at']) >= datetime.fromisoformat(self.activation['at'])):
            raise ValueError('direction/source binding mismatch')
        source_rows = events.RealEventStore(self.source_path, read_only=True)._rows()
        if (not source_rows or source_rows[0]['kind'] != 'discovery_binding'
                or source_rows[0]['data'].get('path') != str(self.path)
                or source_rows[0]['data'].get('authority_id') not in self.authority_ids):
            raise ValueError('source binding missing or conflicting')
        if sum(r['kind'] == 'baseline' for r in rows) > 1:
            raise ValueError('conflicting baseline')

    @classmethod
    def activate(cls, root, operator_root, *, role):
        if role is not DatasetRole.PILOT:
            raise ValueError('PILOT only')
        _guard(root, operator_root)
        _, authority, source, _, binding = _open(operator_root, role)
        source_path = Path(binding['data']['event_journal']).resolve()
        _guard(source_path)
        if source_path.exists():
            raise ValueError('source journal already exists; no mixing histories')
        root = Path(root).resolve()
        if root == Path(operator_root).resolve() or source_path.is_relative_to(root):
            raise ValueError('discovery/source/direction paths must be separate')
        root.mkdir(parents=True, exist_ok=False)
        journal = events.RealEventStore(root / 'discovery.sqlite')
        journal._append('discovery_authority', dict(contract=CONTRACT, contract_hash=CONTRACT_HASH,
            operator_root=str(Path(operator_root).resolve()), source_path=str(source_path),
            direction_authority_id=authority.authority_id, operator_binding=digest(binding)), lambda rows, at: None)
        authority_id = digest(journal._rows()[0])
        # Bind this empty canonical source journal to exactly one discovery authority.
        with source_path.open('xb'):
            pass
        source = events.RealEventStore(source_path)
        source._append('discovery_binding', dict(path=str(root / 'discovery.sqlite'), authority_id=authority_id),
                       lambda rows, at: None)
        return cls(root)

    @classmethod
    def supersede(cls, root, *, contract=CONTRACT_V2, reason=REVISION_REASON):
        """Revise the ACTIVE contract on the SAME authority and journal (append-only).

        Never rebaselines, never renumbers and never deletes: the previous authority,
        its baseline, its discoveries and its document failures stay untouched.
        Live activation is an owner decision and is deliberately not performed here.
        """
        current = cls(root)
        if type(contract) is not dict or contract not in CONTRACT_CHAIN.values() \
                or digest(contract) not in CONTRACT_CHAIN:
            raise ValueError('unknown contract revision')
        if digest(contract) == current.active_contract_hash:
            raise ValueError('contract already active')
        record = supersession_record(previous_authority_id=current.active_authority_id,
                                     previous_contract_hash=current.active_contract_hash,
                                     contract=contract, reason=reason)
        with _lock(current.root):
            fresh = cls(root)
            if fresh.active_contract_hash != current.active_contract_hash:
                raise ValueError('concurrent contract revision')
            fresh._write(SUPERSESSION_KIND, record)
        return cls(root)

    def _write(self, kind, data):
        events.RealEventStore(self.path)._append(kind, data, lambda rows, at: None)

    def poll(self):
        with _lock(self.root):
            current = SourceDiscoveryAuthorityV1(self.root)
            rows = current.journal._rows()
            starts = [r for r in rows if r['kind'] == 'attempt']
            if starts and events._now() < datetime.fromisoformat(starts[-1]['at']) + timedelta(seconds=INTERVAL):
                raise ValueError('next normal 5-minute poll required')
            if any(r['kind']=='feed' for r in rows) and not any(r['kind']=='baseline' for r in rows):
                raise ValueError('interrupted initial watermark; no automatic repair')
            attempt_id = digest((self.authority_id, len(starts)))
            self._write('attempt', dict(attempt_id=attempt_id))
            try:
                raw, received, kind = _fetch(ENDPOINT, feed=True,
                                             user_agent=current.active_contract['user_agent'])
                items = _parse(raw)
                if not datetime.fromisoformat(self.activation['at']) < received <= events._now():
                    raise ValueError('INVALID_FEED: noncausal observation')
                snapshot = dict(attempt_id=attempt_id, received_at=received.isoformat(),
                                raw=raw.decode('utf-8'), content_hash=hashlib.sha256(raw).hexdigest(), items=items)
                self._write('feed', snapshot)
                feed_row = self.journal._rows()[-1]
                baseline = next((r for r in rows if r['kind'] == 'baseline'), None)
                if baseline is None:
                    self._write('baseline', dict(feed_hash=digest(feed_row), items=items))
                    status, count = 'SUCCESS_NO_NEW_ITEMS', 0
                else:
                    blocked_ids = {i['item_id'] for i in baseline['data']['items']}
                    blocked_links = {i['link'] for i in baseline['data']['items']}
                    discoveries = {r['data']['item']['item_id']: r for r in rows if r['kind'] == 'discovery'}
                    count, failures, pending = 0, [], []
                    # Persist every discovery before any document request. On restart,
                    # an earlier durable feed preserves first observation chronology.
                    for item in items:
                        if item['item_id'] in blocked_ids or item['link'] in blocked_links:
                            continue
                        known = discoveries.get(item['item_id'])
                        if known and known['data']['item']['link'] != item['link']:
                            raise ValueError('INVALID_SCOPE: GUID changed document')
                        if not known and any(r['data']['item']['link'] == item['link'] for r in discoveries.values()):
                            raise ValueError('INVALID_SCOPE: document changed GUID')
                        if known is None:
                            first_feed = next(r for r in self.journal._rows() if r['kind']=='feed'
                                and datetime.fromisoformat(r['at']) > datetime.fromisoformat(baseline['at'])
                                and any(i['item_id']==item['item_id'] and i['link']==item['link'] for i in r['data']['items']))
                            first_item = next(i for i in first_feed['data']['items'] if i['item_id']==item['item_id'])
                            self._write('discovery', dict(item=first_item, feed_hash=digest(first_feed),
                                first_seen_at=first_feed['data']['received_at'], authority_id=self.authority_id))
                            known = self.journal._rows()[-1]
                            discoveries[item['item_id']] = known
                            count += 1
                        pending.append(known)
                    for known in pending:
                        try:
                            _capture(current, known, feed_row)
                        except (ValueError, OSError, UnicodeError) as exc:
                            failure = _failure(exc, document=True)
                            failures.append(failure)
                            self._write('document_failure', dict(attempt_id=attempt_id, discovery_id=digest(known), status=failure))
                            if isinstance(exc, HTTPError) and exc.code in (403, 429, 503):
                                break
                    status = 'DOCUMENT_FETCH_FAILURE' if failures else ('SUCCESS_NEW_ITEMS' if count else 'SUCCESS_NO_NEW_ITEMS')
                self._write('result', dict(attempt_id=attempt_id, status=status, new_documents=count))
            except (ValueError, OSError, UnicodeError, ET.ParseError) as exc:
                self._write('result', dict(attempt_id=attempt_id, status=_failure(exc), new_documents=None))
            return self.status()

    def status(self):
        rows = self.journal._rows()
        baseline = next((r for r in rows if r['kind'] == 'baseline'), None)
        starts = [r for r in rows if r['kind'] == 'attempt']
        results = [r for r in rows if r['kind'] == 'result']
        last = next((r for r in reversed(results) if starts and r['data']['attempt_id'] == starts[-1]['data']['attempt_id']), None)
        receipts = inbox(self.root)
        return dict(authority_id=self.authority_id, activated_at=self.activation['at'], contract_hash=CONTRACT_HASH,
            active_authority_id=self.active_authority_id, active_contract_hash=self.active_contract_hash,
            contract_revisions=len(self.supersessions),
            supersedes_authority_id=(self.supersessions[-1]['data']['previous_authority_id'] if self.supersessions else None),
            endpoint_hash=digest(ENDPOINT), role='PILOT', scope=SCOPE, source_path=str(self.source_path),
            baseline_established=baseline is not None, baseline_count=len(baseline['data']['items']) if baseline else 0,
            baseline_hash=digest(baseline) if baseline else None,
            last_poll=starts[-1]['at'] if starts else None, last_status=last['data']['status'] if last else ('INCOMPLETE' if starts else 'NOT_ATTEMPTED'),
            new_documents=sum(r['kind']=='discovery' for r in rows), receipts=len(receipts),
            admitted_candidates=sum(r['admission_status']=='ADMITTED' for r in receipts),
            unattested_candidates=sum(r['admission_status']=='ADMITTED' and r['attestation_status']=='MISSING' for r in receipts),
            integrity='PASS')


def _failure(exc, document=False):
    if isinstance(exc, HTTPError): return 'HTTP_FAILURE'
    if isinstance(exc, (URLError, OSError)): return 'NETWORK_FAILURE'
    if 'INVALID_SCOPE' in str(exc): return 'INVALID_SCOPE'
    return 'INVALID_DOCUMENT' if document else 'INVALID_FEED'


def _capture(authority, discovery, feed_row):
    """Private: no arbitrary URL/content/timestamp capture entry point."""
    rows = authority.journal._rows()
    if discovery not in rows or feed_row not in rows or discovery['kind'] != 'discovery':
        raise ValueError('authenticated discovery required')
    item = discovery['data']['item']
    if not any(i['item_id']==item['item_id'] and i['link']==item['link'] for i in feed_row['data']['items']):
        raise ValueError('document absent from current feed')
    source = events.RealEventStore(authority.source_path)
    existing = source._rows()
    if (not existing or existing[0]['kind'] != 'discovery_binding'
            or existing[0]['data'].get('path') != str(authority.path)
            or existing[0]['data'].get('authority_id') not in authority.authority_ids):
        raise ValueError('source discovery binding mismatch')
    url = _url(item['link'])
    name = digest((SCOPE, url))
    source_row = next((r for r in existing if r['kind']=='source' and r['data']['source']==name), None)
    if source_row is None:
        source._append('source', dict(source=name,version=SCHEMA,url=url,content_kind='FULL_DOCUMENT',
            discovery_authority=authority.authority_id, discovery_id=digest(discovery)), lambda rows,at:None)
        source_row = source._rows()[-1]
    raw, received, kind = _fetch(url, feed=False,
                                 user_agent=authority.active_contract['user_agent'])
    if not datetime.fromisoformat(source_row['at']) < received <= events._now():
        raise ValueError('noncausal document observation')
    content = raw.decode('utf-8', errors='strict')
    content_hash = hashlib.sha256(raw).hexdigest()
    previous = [r for r in existing if r['kind']=='receipt' and r['data']['source']==name]
    if previous and previous[-1]['data']['content_hash']==content_hash:
        # Verification never repairs an interrupted ready marker.
        return source.receipt(previous[-1]['data']['receipt_id'])
    prior_id = previous[-1]['data']['receipt_id'] if previous else None
    revision = digest((digest(discovery), prior_id, content_hash))
    identity = digest((events.REAL_VERSION,name,SCHEMA,url,revision))
    proof = dict(path=str(authority.path), authority_id=authority.authority_id,
                 discovery_id=digest(discovery), feed_hash=digest(feed_row), prior_receipt_id=prior_id)
    payload = dict(receipt_id=identity,source=name,source_version=SCHEMA,document_id=url,revision_id=revision,
        content=content,content_hash=content_hash,content_kind='FULL_DOCUMENT',role='PILOT',
        received_at=received.isoformat(),source_authorization=digest(source_row),response_content_type=kind,
        final_url=url,discovery_proof=proof)
    source._append('receipt',payload,lambda rows,at:None)
    source._append('ready',dict(receipt_id=identity),lambda rows,at:None)
    return source.receipt(identity)


def verify_receipt_proof(source_path, receipt_row, source_rows):
    p=receipt_row['data']; proof=p['discovery_proof']
    authority=SourceDiscoveryAuthorityV1(Path(proof['path']).parent)
    if (authority.path != Path(proof['path']).resolve()
            or authority.source_path != Path(source_path).resolve()
            or proof['authority_id'] not in authority.authority_ids):
        raise ValueError('discovery provenance mismatch')
    rows=authority.journal._rows()
    discovery=next((r for r in rows if r['kind']=='discovery' and digest(r)==proof['discovery_id']),None)
    feed=next((r for r in rows if r['kind']=='feed' and digest(r)==proof['feed_hash']),None)
    baseline=next((r for r in rows if r['kind']=='baseline'),None)
    if discovery is None or feed is None or baseline is None:
        raise ValueError('missing discovery evidence')
    item=discovery['data']['item']
    original_feed=next((r for r in rows if r['kind']=='feed' and digest(r)==discovery['data']['feed_hash']),None)
    baseline_feed=next((r for r in rows if r['kind']=='feed' and digest(r)==baseline['data']['feed_hash']),None)
    for evidence in (feed, original_feed, baseline_feed):
        if evidence is None:
            raise ValueError('missing feed provenance')
        raw=evidence['data']['raw'].encode('utf-8')
        if hashlib.sha256(raw).hexdigest()!=evidence['data']['content_hash'] or _parse(raw)!=evidence['data']['items']:
            raise ValueError('feed evidence mismatch')
    if (baseline['data']['items']!=baseline_feed['data']['items'] or item not in original_feed['data']['items']
            or discovery['data']['first_seen_at']!=original_feed['data']['received_at']):
        raise ValueError('first discovery provenance mismatch')
    if any(i['item_id']==item['item_id'] or i['link']==item['link'] for i in baseline['data']['items']):
        raise ValueError('baseline cannot produce receipt')
    if (p['role']!='PILOT' or p['document_id']!=item['link'] or p['final_url']!=item['link']
            or not any(i['item_id']==item['item_id'] and i['link']==item['link'] for i in feed['data']['items'])):
        raise ValueError('discovery scope/role mismatch')
    source=next((r for r in source_rows if r['kind']=='source' and digest(r)==p['source_authorization']),None)
    if source is None or source['data'].get('discovery_id')!=digest(discovery):
        raise ValueError('source commitment mismatch')
    times=[authority.activation['at'],baseline['at'],discovery['data']['first_seen_at'],discovery['at'],
           feed['at'],p['received_at'],receipt_row['at']]
    # First discovery can be appended after its feed row, whereas later revision feeds are later.
    a,b,f,d,feed_at,received,persisted=map(datetime.fromisoformat,times)
    if not (a<=b<f<=d<=received<=persisted and feed_at<=received):
        raise ValueError('noncausal discovery evidence')
    previous=[r for r in source_rows[:source_rows.index(receipt_row)] if r['kind']=='receipt' and r['data']['source']==p['source']]
    prior=previous[-1]['data']['receipt_id'] if previous else None
    revision=digest((digest(discovery),prior,p['content_hash']))
    if proof['prior_receipt_id']!=prior or p['revision_id']!=revision or p['receipt_id']!=digest((events.REAL_VERSION,p['source'],SCHEMA,p['document_id'],revision)):
        raise ValueError('revision identity mismatch')


def inbox(root):
    authority=SourceDiscoveryAuthorityV1(root)
    if not authority.source_path.exists(): return []
    source=events.RealEventStore(authority.source_path,read_only=True)
    source_rows=source._rows(); replay=source._replay(source_rows)
    _, direction, _, direction_rows, _=_open(authority.activation['data']['operator_root'],DatasetRole.PILOT)
    result=[]
    for row in source_rows:
        if row['kind']!='receipt': continue
        r=source.receipt(row['data']['receipt_id'])
        c=next((c for c in replay.candidates() if c.envelope.receipt_id==r.receipt_id),None)
        reservation=next((v for v in replay.reservations() if c and v.reservation_id==c.reservation_id),None)
        status='AWAITING_MANUAL_ADMISSION' if c is None else ('ADMITTED' if reservation and not c.reasons and replay.sampling_eligible(reservation.reservation_id,reservation.decision_at) else 'REJECTED')
        attestation='MISSING'
        if any(x['kind']=='direction' and x['data']['receipt_id']==r.receipt_id for x in direction_rows):
            try: direction.verify(source,r.receipt_id); attestation='VERIFIED'
            except ValueError: attestation='INVALID'
        discovery=next(x for x in authority.journal._rows() if x['kind']=='discovery' and digest(x)==row['data']['discovery_proof']['discovery_id'])
        result.append(dict(receipt_id=r.receipt_id,event_id=c.envelope.event_id if c else None,source=r.source,
            document_id=r.document_id,title=discovery['data']['item']['title'],content=r.content,
            received_at=r.received_at.isoformat(),available_at=r.available_at.isoformat() if r.available_at else None,
            decision_at=reservation.decision_at.isoformat() if reservation else None,
            admission_status=status,attestation_status=attestation))
    return result
