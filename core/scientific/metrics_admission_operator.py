"""Prospective PILOT admission; one-shot, no HTTP, no historical promotion.

TEST_ONLY authorities cannot bind production paths or report a real path.
Production deployment is pinned to the project's Windows runtime convention.
"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from . import metrics_h1_runner as runner
from . import metrics_continuity as continuity
from .metrics_observation_bundle import load_verified_bundle
from .metrics_observation_admission import admit_verified_metrics_bundle
from .metrics_publication import observation_snapshot, publication_for
from .metrics_snapshot_gate import metrics_snapshot_available
from .causal_mechanics import append_causal_mechanics
from .prospective_receipts import canonical_observation as canonical, observation_hash as digest, _utc

SCHEMA = 'metrics-admission-authority-v1'
HOUR = timedelta(hours=1)
PRODUCTION = Path.home()/'Documents'/'O-C data'/'prospective'
RUNTIME = Path.home()/'Documents'/'OMA-CORE-RUNTIME-METRICS51'
REPO = Path(__file__).resolve().parents[2]
FILES = ('core/scientific/metrics_admission_operator.py', 'scripts/metrics_admission.py',
 'core/scientific/metrics_observation_admission.py', 'core/scientific/metrics_publication.py',
 'core/scientific/metrics_snapshot_gate.py', 'core/scientific/metrics_observation_bundle.py',
 'core/scientific/metrics_continuity.py', 'core/scientific/metrics_h1_runner.py',
 'core/scientific/metrics_h1_activation.py', 'core/scientific/prospective_receipts.py',
 'core/scientific/causal_mechanics.py', 'core/scientific/causal_observation_snapshot.py',
 'core/scientific/experiment51_derived.py')


def _now(): return datetime.now(timezone.utc)


def _path(value):
    p=Path(value)
    if not p.is_absolute() or '..' in p.parts: raise ValueError('absolute canonical path required')
    if os.environ.get('PYTEST_CURRENT_TEST') and (p==PRODUCTION or PRODUCTION in p.parents):
        raise ValueError('tests cannot access production prospective state')
    from .metrics_h1_activation import _reject_aliases
    _reject_aliases(p)
    return p.resolve()


def _contracts(config):
    hashes={name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in FILES}
    return dict(capture_contract_hash=digest(config),
        admission_contract_hash=hashes['core/scientific/metrics_observation_admission.py'],
        durable_publication_contract_hash=hashes['core/scientific/metrics_publication.py'],
        contract_hash=digest(hashes))


def _deployment(root, source, mode):
    if mode=='TEST_ONLY':
        if any(p==PRODUCTION or PRODUCTION in p.parents for p in (root,source)):
            raise ValueError('test authority cannot access production')
        return 'TEST_ONLY'
    if mode!='PROSPECTIVE' or os.name!='nt' or REPO!=RUNTIME:
        raise ValueError('prospective authority requires pinned Windows runtime')
    if root!=PRODUCTION/'metrics-admission-v1' or source!=PRODUCTION/'metrics-h1-v1':
        raise ValueError('production state binding mismatch')
    branch=subprocess.run(['git','symbolic-ref','-q','HEAD'],cwd=REPO,capture_output=True,text=True)
    if branch.returncode!=1: raise ValueError('runtime must be detached')
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()


class MetricsAdmissionAuthorityV1:
    def __init__(self, root):
        self.root=_path(root)
        raw=_path(self.root/'authority.json').read_text(encoding='utf-8')
        _path(self.root/'observations.sqlite');_path(self.root/'attempts.sqlite')
        body=json.loads(raw)
        source=_path(body['source_state_binding'])
        runtime=_deployment(self.root,source,body['environment'])
        config=runner.load_config(source,repo_root=REPO)
        expected=dict(schema=SCHEMA,dataset_role='PILOT',activated_at=_utc(body['activated_at']).isoformat(),
            source_state_binding=str(source),observations_v2_binding=str(self.root/'observations.sqlite'),
            state_root=str(self.root),environment=body['environment'],runtime_commit=runtime,**_contracts(config))
        expected['authority_id']=digest(expected)
        if body!=expected or raw!=canonical(expected) or config['dataset_role']!='PILOT':
            raise ValueError('authority/role/contract/binding integrity failure')
        self._raw=raw

    @property
    def body(self): return json.loads(self._raw)

    @classmethod
    def activate(cls, root, source, *, role='PILOT', environment='PROSPECTIVE'):
        root,source=_path(root),_path(source)
        if role!='PILOT': raise ValueError('PILOT only')
        runtime=_deployment(root,source,environment)
        if root==source or root in source.parents or source in root.parents or root==REPO or REPO in root.parents:
            raise ValueError('admission/capture/repository separation required')
        config=runner.load_config(source,repo_root=REPO)
        if config['dataset_role']!='PILOT': raise ValueError('capture role mismatch')
        contracts=_contracts(config)
        root.mkdir()  # exclusive; no overwrite, no pre-existing ledger adoption
        body=dict(schema=SCHEMA,dataset_role='PILOT',activated_at=_utc(_now()).isoformat(),
            source_state_binding=str(source),observations_v2_binding=str(root/'observations.sqlite'),
            state_root=str(root),environment=environment,runtime_commit=runtime,**contracts)
        body['authority_id']=digest(body)
        with (root/'authority.json').open('x',encoding='utf-8',newline='') as f:
            f.write(canonical(body));f.flush();os.fsync(f.fileno())
        return cls(root)

    def _open(self):
        fresh=type(self)(self.root)
        if fresh._raw!=self._raw: raise ValueError('authority changed')
        if _utc(_now())<_utc(fresh.body['activated_at']): raise ValueError('clock precedes authority activation')
        return fresh.body

    def _journal(self):
        p=self.root/'attempts.sqlite'
        if not p.exists(): return []
        with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as con:
            values=con.execute('SELECT body,previous_hash,hash FROM entries ORDER BY seq').fetchall()
        previous='0'*64; result=[]
        for raw,link,h in values:
            if link!=previous or digest([link,raw])!=h: raise ValueError('journal integrity failure')
            body=json.loads(raw)
            if body['authority_id']!=self.body['authority_id']: raise ValueError('journal authority mismatch')
            result.append(body);previous=h
        return result

    def _append(self, kind, data, *, claim=False):
        self._open()
        con=sqlite3.connect(self.root/'attempts.sqlite',timeout=10)
        try:
            con.execute('PRAGMA synchronous=FULL')
            con.execute('CREATE TABLE IF NOT EXISTS entries(seq INTEGER PRIMARY KEY,body TEXT,previous_hash TEXT,hash TEXT)')
            for op in ('UPDATE','DELETE'):
                con.execute(f"CREATE TRIGGER IF NOT EXISTS journal_no_{op.lower()} BEFORE {op} ON entries BEGIN SELECT RAISE(ABORT,'append-only'); END")
            con.execute('BEGIN IMMEDIATE')
            rows=self._journal()
            if claim and any(r['kind']=='START' and r['data']['slot']==data['slot'] for r in rows):
                raise ValueError('slot already claimed; no retry or repair')
            last=con.execute('SELECT hash FROM entries ORDER BY seq DESC LIMIT 1').fetchone()
            previous=last[0] if last else '0'*64
            body=dict(kind=kind,authority_id=self.body['authority_id'],at=_utc(_now()).isoformat(),data=data)
            raw=canonical(body)
            con.execute('INSERT INTO entries(body,previous_hash,hash) VALUES (?,?,?)',(raw,previous,digest([previous,raw])))
            con.commit()
        finally: con.close()

    def inventory(self):
        b=self._open();now=_utc(_now());A=_utc(b['activated_at']);source=Path(b['source_state_binding'])
        config=runner.load_config(source,repo_root=REPO);slot=_utc(config['activation_slot']);items=[]
        while slot<=now.replace(minute=0,second=0,microsecond=0):
            check=continuity.verify_slot(source,slot,repo_root=REPO,now=now)
            # Capture receipt chronology, never scan cadence, determines the boundary.
            post = slot+timedelta(seconds=180)>A
            if check['status']=='SUCCESS':
                bundle=json.loads(load_verified_bundle(source,slot,repo_root=REPO,now=now).canonical_json)
                post=all(_utc(c['request_started_at'])>A for c in bundle['components'].values())
            boundary='POST_AUTHORITY_CAPTURE' if post else 'PRE_AUTHORITY_CAPTURE'
            items.append(dict(slot=slot.isoformat(),capture_status=check['status'],boundary=boundary))
            slot+=HOUR
        return items

    def once(self):
        b=self._open();started=_utc(_now());source=Path(b['source_state_binding']);ledger=Path(b['observations_v2_binding'])
        inventory=self.inventory();prior=self._journal();results=[]
        for item in inventory:
            slot=_utc(item['slot'])
            if item['boundary']!='POST_AUTHORITY_CAPTURE' or item['capture_status']!='SUCCESS': continue
            previous=[r for r in prior if r['kind']=='START' and r['data']['slot']==item['slot']]
            if previous:
                terminal=[r['data'] for r in prior if r['kind']=='RESULT' and r['data']['slot']==item['slot']]
                if terminal and terminal[-1]['status']=='ADMITTED':
                    rows,_=observation_snapshot(ledger)
                    p=publication_for(rows,terminal[-1]['bundle_id'])
                    if p['publication_id']!=terminal[-1]['publication_id']: raise ValueError('publication conflict')
                    results.append(dict(slot=item['slot'],status='ALREADY_ADMITTED',publication_id=p['publication_id']))
                else: results.append(dict(slot=item['slot'],status='TERMINAL_OR_INCOMPLETE_NO_RETRY'))
                continue
            # The qualified admission contract retains its existing 24-hour bound.
            # Delayed publication never qualifies an earlier decision.
            self._append('START',dict(slot=item['slot'],worker_started_at=started.isoformat()),claim=True)
            result=dict(slot=item['slot'],worker_started_at=started.isoformat(),status='FAILED_VALIDATION')
            try:
                bundle=load_verified_bundle(source,slot,repo_root=REPO,now=_now());raw=json.loads(bundle.canonical_json)
                if raw['dataset_role']!='PILOT' or any(_utc(c['request_started_at'])<=_utc(b['activated_at']) for c in raw['components'].values()):
                    raise ValueError('post-authority capture required')
                result.update(bundle_id=bundle.bundle_id,capture_identity=raw['capture_receipt_id'])
                self._open()  # contract and authority unchanged immediately before admission
                admitted=admit_verified_metrics_bundle(ledger,source,slot,repo_root=REPO,now=_now())
                rows,_=observation_snapshot(ledger);p=publication_for(rows,bundle.bundle_id)
                cutoff=_utc(_now())
                if not all(metrics_snapshot_available(rows,i,cutoff) for i in p['observation_ids']):
                    raise ValueError('durable publication unavailable')
                result.update(status='ADMITTED',observation_ids=p['observation_ids'],publication_id=p['publication_id'],
                    published_at=p['published_at'],effective_available_at=max(p['published_at'],raw['capture_available_at']),mechanics_id=None)
                # Persistence after the raw cutoff is honest, but cannot manufacture a timely input.
                raw_cut=min(cutoff,slot+timedelta(minutes=5))
                if all(metrics_snapshot_available(rows,i,raw_cut) for i in p['observation_ids']):
                    mech=append_causal_mechanics(ledger,dataset_role='PILOT',cutoff=raw_cut,clock=_now)
                    result['mechanics_id']=mech['id']
                else: result['mechanics_reason']='PUBLICATION_AFTER_FROZEN_RAW_CUTOFF'
            except (ValueError,KeyError,TypeError,OSError,sqlite3.Error) as error:
                result['status']='FAILED_VALIDATION';result['error']=str(error)
                if ledger.exists():
                    from .prospective_receipts import observation_snapshot as physical
                    physical_rows,_=physical(ledger,read_only=True)
                    if any(r.get('provenance',{}).get('bundle_id')==result.get('bundle_id') for r in physical_rows.values()):
                        result['status']='PUBLICATION_OR_DERIVATION_FAILED_NO_REPAIR'
            result['worker_completed_at']=_utc(_now()).isoformat()
            self._append('RESULT',result);results.append(result)
        output=dict(status='PROCESSED' if results else 'NO_ELIGIBLE_BUNDLES',results=results,
            pre_authority_valid=sum(i['boundary']=='PRE_AUTHORITY_CAPTURE' and i['capture_status']=='SUCCESS' for i in inventory),
            worker_started_at=started.isoformat(),worker_completed_at=_utc(_now()).isoformat())
        self._append('SCAN',output)
        return output

    def status(self):
        b=self._open();items=self.inventory();journal=self._journal();ledger=Path(b['observations_v2_binding']);now=_utc(_now())
        admitted=[]
        rows,_=observation_snapshot(ledger) if ledger.exists() else ({},[])
        for entry in journal:
            if entry['kind']!='RESULT' or entry['data']['status']!='ADMITTED': continue
            r=entry['data'];p=publication_for(rows,r['bundle_id'])
            if p['publication_id']!=r['publication_id'] or not all(metrics_snapshot_available(rows,i,now) for i in p['observation_ids']):
                raise ValueError('recorded admission lacks valid causal publication')
            admitted.append(r)
        report=continuity.status(b['source_state_binding'],repo_root=REPO,now=now)
        return dict(schema='metrics-admission-status-v1',authority=b,continuity=report,
            PRE_AUTHORITY_VALID_CAPTURES=sum(i['boundary']=='PRE_AUTHORITY_CAPTURE' and i['capture_status']=='SUCCESS' for i in items),
            POST_AUTHORITY_VALID_CAPTURES=sum(i['boundary']=='POST_AUTHORITY_CAPTURE' and i['capture_status']=='SUCCESS' for i in items),
            POST_AUTHORITY_ATOMIC_BUNDLES_ADMITTED=len(admitted),LATEST_ADMITTED_METRICS_SLOT=admitted[-1]['slot'] if admitted else None,
            LATEST_ADMITTED_BUNDLE_ID=admitted[-1]['bundle_id'] if admitted else None,
            TAKER_REAL_INPUTS_AVAILABLE=len(admitted) if b['environment']=='PROSPECTIVE' else 0,
            MECHANICS_REAL_PATH_OBSERVED=bool(admitted) and b['environment']=='PROSPECTIVE',
            METRICS_REAL_READY=False,MECHANICS_REAL_READY=False,EXPERIMENT_51_READY=False,
            readiness_reason='Experiment 51 population/common support gates not evaluated by admission status',
            last_scan=next((r['data'] for r in reversed(journal) if r['kind']=='SCAN'),None))
