# Continuous prospective H1 Price capture

Initial checkpoint: `7a95a6615ea7da509e0a9c23da1ad1229e0fca47`, main.
This is engineering infrastructure, not a trading experiment. Historical Data
Gate remains FAIL; Mechanics freeze is unchanged; MM READY=0/BLOCKED=10.
No Regime, outcomes, Knowledge promotion or Criterion updates are executed.
Binance 2025 and Kraken Q2-2026 were not opened.

## Operation and recovery

`scripts/capture_price_h1.py` calculates UTC hourly boundaries plus a default
5-second safety delay (configurable 0–60 seconds). It waits in at most 20-second
increments, checking wall-clock regression. Each capture makes two public calls:
server time then the latest closed BTCUSDT USD-M H1 kline. It never requests a
historical range, metrics, funding or outcomes. The scheduler does not assign
receipt availability: the existing persistence contract does.

There is one retry, 20 seconds after a failed attempt, only within the two-minute
slot window. A process restarted inside that window can retry the current slot;
later restarts wait for the next boundary. Missed bars remain gaps. Host sleep,
logout, outage and long downtime can therefore reset the streak. There is no
guarantee of uninterrupted capture while the host is unavailable.

An OS file lock prevents concurrent runners; SQLite preserves the first receipt
for identical identities/payloads and rejects conflicting payloads. Intent/result
files preserve attempts and conflicts outside SQLite. Unfinished intent means
interrupted/unknown attempt; ledger state remains the authority on whether a
receipt committed. A persisted conflict blocks certification until an explicitly
audited resolution; the runner never silently clears it. Detectable clock
regression fails closed. Correct the host clock before restarting.

The installed Windows task `OMA-CORE-Prospective-Price-H1` runs as the current
user, with no stored password and no elevation. It starts at user logon, restarts
on process failure after one minute (up to 999 retries), and ignores simultaneous
starts. It uses pythonw to avoid a visible console. It is not a pre-logon service:
after reboot, the user must sign in. The computer must remain awake and online.
The task and runtime are machine-local and are not transported by Git.

Paths on this host:

- Python: `C:\Users\KiTO\Documents\O-C data\prospective\runtime\Scripts\python.exe`
- Ledger: `C:\Users\KiTO\Documents\O-C data\prospective\receipts.db`
- State: `C:\Users\KiTO\Documents\O-C data\prospective\continuous`

Start/restart the installed task:

```powershell
Start-ScheduledTask -TaskName 'OMA-CORE-Prospective-Price-H1'
```

Status, with freshly verified ledger, causal gate and anchors:

```powershell
& 'C:\Users\KiTO\Documents\O-C data\prospective\runtime\Scripts\python.exe' 'C:\Users\KiTO\Documents\OMA-CORE\scripts\capture_price_h1.py' status --ledger 'C:\Users\KiTO\Documents\O-C data\prospective\receipts.db' --state 'C:\Users\KiTO\Documents\O-C data\prospective\continuous' --json
```

Omit `--json` for human-readable output. `capture_running` checks the OS lock;
`runner.at` and `next_capture_at` show heartbeat freshness, not proof of network
health. Inspect `attempts/` and `errors/` after faults. `status.json` is a cache;
the command recomputes it. Do not confuse a previously saved certificate with
current readiness after later gaps.

Independent foreground execution uses the same command with `run` instead of
`status` and without `--json`. It refuses a second runner while the task is active.

Reinstall on this host (also starts it):

```powershell
& 'C:\Users\KiTO\Documents\OMA-CORE\scripts\install_price_capture_task.ps1' -Python 'C:\Users\KiTO\Documents\O-C data\prospective\runtime\Scripts\python.exe'
```

On another host create a persistent Python 3.12+ environment, install
`scripts/requirements-price-capture.txt`, and supply local `-Python`, `-Ledger`,
`-State` paths. Transfer the ledger using SQLite's backup facility while live
(or stop the runner and checkpoint WAL first), along with all anchors and attempt
logs. Verify status before restarting. Never copy only a live `.db` while ignoring
its WAL. The local venv uses the app-managed base Python; if that base runtime is
removed, recreate the venv and re-register the task. No Work session is needed.

## Continuity and certificate semantics

The checker scans one hash-verified snapshot and uses the existing causal gate.
Only raw BTCUSDT Price/OHLCV receipts count. Event time must equal the latest
closed UTC hour at request, server-time sample and receipt; older fetched bars
cannot repair a gap. UNKNOWN, malformed, open, future, mismatched or failed-gate
receipts are excluded. Duplicate hours are excluded and reported; acquisition
order regressions are reported and conservatively block certification.

The streak requires one-hour differences. Forty valid bars, one missed hour and
41 valid bars yield current streak 41, not 81. Missing hours through the latest
due boundary (including safety delay) appear in status; a pending request can
briefly show the current hour missing until its real receipt commits. Longest
streak is historical; current streak is zero when the last due hour is absent.

At current streak >=81, the latest 81 valid contiguous receipts produce an
immutable certificate in `certificates/<certified_set_hash>.json`. It contains
IDs, set hash, chain head/count, timestamps, contract and gate/continuity code
hashes. Same ledger/reference/code produces the same certificate; the first
certificate per window is retained. Earlier gaps outside that window do not
invalidate it. Eighty bars or an invalid/gapped window never certify.

`REGIME_INPUT_READY` means sufficient causal Price inputs only. It does not
execute or validate Regime, make MM ready, or demonstrate Edge. Synthetic test
fixtures are never added to the real ledger.

## External anchors and trust model

`anchors/<count>-<head>.json` is created once per new ledger head, with timestamp,
count, last event/ID, contract and self-hash. Every status verifies that the ledger
contains each anchored prefix. Normal extension passes; chain corruption,
rewriting a prefix or rollback behind an anchor fails. No hourly Git commits.
An initial anchor is also versioned in this checkpoint as an independent baseline.

Local anchors and attempt logs are exportable tamper evidence, not a trusted
timestamping service. A party controlling SQLite **and** every external copy can
rewrite both. Preserve exported anchors separately/off-host for stronger evidence.
Deleting all local anchors is not inherently detectable without an independently
retained baseline; compare the versioned baseline too. A partial/corrupt anchor
fails closed and requires investigation; do not delete it to force a pass.
Host clock, TLS and operating-system integrity remain explicit trust assumptions.

## Verified checkpoint state

47 focused tests pass (46 together plus the final scheduled-slot rejection test).
Freeze verification passes while Data Gate remains FAIL. No full suite was
rerun: this checkpoint changes receipt infrastructure only. A real task restart
was verified without adding or altering the existing receipt.

As of 2026-09-30 18:50 UTC: task RUNNING, next capture 19:00:05 UTC;
one real receipt (event 18:00 UTC), current streak 1, gaps/conflicts/invalid 0,
80 remaining, certificate NOT READY, Regime BLOCKED. No new real bar was
manufactured or fetched to fill time. See the small status/anchor checkpoint in
`research/edge_discovery/price_point_in_time/continuous_capture/`.
