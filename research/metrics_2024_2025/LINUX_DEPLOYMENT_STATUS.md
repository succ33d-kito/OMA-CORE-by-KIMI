# Linux Mint deployment readiness — 2026-09-29

Prepared an unprivileged systemd user service and UTC five-minute timer installer, a read-only preflight, a hard 2026-10-01 UTC start guard, and a collection health report. The timer has `Persistent=false`; missed intervals are never backfilled. The unit syntax and calendar expression were verified locally with `systemd-analyze`, and the full Python suite passed (1,012 passed, 12 skipped).

**Not installed or activated on the user's computer.** Work mode has no access to that machine. This execution environment received Binance HTTP 451, so no prospective observations were collected and no gate was evaluated. The host must pass the market-data preflight and have authorized access to the top-trader fields before activating. The laptop must remain on Linux, awake and connected to collect a continuous feed; otherwise missing hours remain missing. See `docs/PROSPECTIVE_LINUX_MINT_DEPLOYMENT.md`.
