'use strict';
const panels = ['system','data','world','radar','decisions','portfolio','execution','positions','science'];
function show(id, value) {
  document.getElementById(id).textContent = JSON.stringify(value, (key,item) => item === null ? 'UNKNOWN' : item, 2);
}
function renderSnapshot(s) {
  const sources = Object.fromEntries(s.sources.map(row => [row.name,row]));
  const missing = {state:'UNAVAILABLE',details:null};
  const collector = sources.collector || missing;
  show('system',{node:s.node,mode:s.mode,snapshot_at:s.snapshot_at,snapshot_id:s.snapshot_id,
    next_cycle:collector.details?.next_cycle ?? null,next_cycle_evidence_state:collector.state});
  show('data',['price','collector','book','premium','events'].map(k => ({component:k,...(sources[k] || missing)})));
  show('world',sources.world || missing);
  show('radar',sources.radar || missing);
  show('decisions',s.decisions);
  show('portfolio',{state:s.decisions.state,freshness:s.decisions.freshness,mode:s.decisions.details?.mode ?? null,
    portfolio:s.decisions.details?.portfolio ?? null,unallocated:s.decisions.details?.allocation?.unallocated ?? null,
    source:s.decisions.source,commitment:s.decisions.commitment});
  show('execution',s.execution);
  show('positions',s.positions);
  show('science',s.science);
  const states = s.sources.map(row => row.state);
  document.getElementById('connection').textContent = states.includes('INVALID') ? 'INVALID evidence present — inspect affected panels' :
    states.every(x => x === 'UNAVAILABLE') ? 'UNAVAILABLE — no configured evidence observed' :
    states.includes('STALE') ? 'STALE evidence present — not current runtime proof' : 'Snapshot loaded — inspect availability and freshness per source';
}
async function refreshSnapshot() {
  document.getElementById('connection').textContent = 'WAITING — reading snapshot';
  try {
    const response = await fetch('/api/system',{method:'GET',cache:'no-store'});
    const snapshot = await response.json();
    if (!response.ok || !snapshot.sources) throw new Error('Snapshot unavailable');
    renderSnapshot(snapshot);
  } catch (_) {
    for (const id of panels) document.getElementById(id).textContent = 'UNKNOWN — snapshot request failed';
    document.getElementById('connection').textContent = 'INVALID / UNAVAILABLE — cannot verify current snapshot';
  }
}
document.getElementById('refresh').addEventListener('click',refreshSnapshot);
refreshSnapshot();
