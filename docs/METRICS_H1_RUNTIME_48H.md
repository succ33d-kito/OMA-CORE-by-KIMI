# STEP 48H — qualified runtime code, not deployment

`metrics_h1_runtime.run_forever` requires previously activated config, explicit
repo root and transport. It never initializes activation, installs tasks or
modifies Price/Funding. Windows file locking excludes duplicate processes and
releases on process death. Heartbeat is replaceable operational metadata, never
market evidence. Polling is bounded to five seconds; no keep-awake behavior.

The clock is guarded through adapter and runner. Restart uses authenticated
heartbeat metadata as a lower-bound operational clock anchor, not a receipt.
Malformed heartbeat/pending publication stops for inspection; it is not repaired
silently. Expected transport failures persist FAILED and allow later slots.
Unexpected config/filesystem/clock failures stop closed. No old attempt resumes.

Tests use injected clocks/sleep/transport and isolated temporary activated roots.
No live runtime was started, no real Metrics state activated, no scheduler touched.
Requests timeout is not a hard whole-call deadline. A blocked system/network call
may delay runtime progress; causal guards prevent late evidence admission, but
hard cancellation and real sleep/power recovery remain deployment-qualification
limitations. The wrapper/installer and controlled live ceremony are separate.
