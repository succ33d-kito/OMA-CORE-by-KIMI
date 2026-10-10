# 48I.1 — Metrics execution wrapper

`scripts/run_metrics_h1.py check --state <absolute activated metrics-h1-v1>`
authenticates the existing frozen configuration without writing state or loading
the HTTP transport. CONFIG_VERIFIED is not runtime liveness or data readiness.

`scripts/run_metrics_h1.py run --state <same path> --allow-public-http`
explicitly binds the qualified public transport to the 48H runtime. It cannot
activate state, select role, override timestamps, backfill, install tasks or
change capture settings. The runtime revalidates config and owns process locking.
Use the qualified Python environment with Requests available for actual run.

This checkpoint uses isolated synthetic activation fixtures and injected runtime;
no real state, network, scheduler or collector was started. The operator activation
ceremony and scheduler installer remain subsequent bounded checkpoints. The
transport inactivity timeout is not a hard total-call deadline; this remains a
deployment qualification limitation. Preserve interrupted artifacts for inspection.

Edge = NO. Regime validation = NO. Mechanics validation = NO.
Real Metrics continuity and 81H readiness remain unverified.
