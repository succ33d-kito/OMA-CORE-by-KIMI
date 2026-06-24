# AI Workflow Rules

## Purpose

These rules ensure all AI assistants working on O.M.A.-C.O.R.E. / OSIRIS share the same project state, avoid conflicting decisions, and maintain consistent documentation.

---

## Rule #1 — Read Project State First

**Every AI assistant must read `project_state.md` before making recommendations or taking actions.**

This ensures the AI knows:
- What phase the project is in
- What constraints are active
- What the current priority is
- What the smoke run status is
- What capital stages are NO-GO

**Failure to read project_state.md first may result in recommending changes that violate active constraints.**

---

## Rule #2 — Repository State Overrides AI Memory

**If the repository state (code, test results, telemetry data) contradicts what the AI remembers or assumes, the repository state wins.**

Examples:
- If tests show 277 passed + 4 skipped, do not claim 281 passed
- If the smoke run is active, do not say it hasn't started
- If guard audit records show "Unknown" sources, do not claim guard attribution is working

**Always verify claims against actual files before asserting them.**

---

## Rule #3 — Architecture Changes Require architecture.md Update

**Any change to the system architecture must also update `architecture.md`.**

This includes:
- Adding or removing modules
- Changing data flow
- Adding new output files
- Changing pipeline structure
- Adding new entry points

The architecture.md must always reflect the current codebase.

---

## Rule #4 — Roadmap Changes Require future_roadmap.md Update

**Any change to project priorities, phases, or timeline must also update `future_roadmap.md`.**

This includes:
- Adding new phases
- Changing phase order
- Marking phases as complete/in progress
- Changing success criteria

---

## Rule #5 — No Flaw Closure Without open_flaws.md Update

**A flaw is only truly closed when `open_flaws.md` is updated to reflect the new status.**

The update must include:
- What the fix was
- What tests verify the fix
- What the new status is (FIXED / PARTIAL / DEFERRED)

---

## Rule #6 — Every Major Sprint Updates completed_work.md and project_state.md

**At the end of every major sprint, both files must be updated:**

- `completed_work.md`: Add what was accomplished, with dates, test counts, and key findings
- `project_state.md`: Update Current Phase, Current Milestone, Current Status, Test Status, Latest Commit, Current Priority, Current Next Step

Minor changes (single bug fix, documentation update) may update only one file.

---

## Workflow Summary

```
Before any session:
  1. Read project_state.md
  2. Check operational_status.md for current run state
  3. Read open_flaws.md for known issues
  4. Read current_priorities.md for priority order

During session:
  5. Follow Rule #2 (repository overrides AI memory)
  6. Make changes within constraints

After any change:
  7. Update relevant documentation per Rules #3-6
  8. Verify tests still pass
```

## File Dependency Map

```
project_state.md          → Must be read FIRST by every AI
architecture.md           → Updated when architecture changes
current_priorities.md     → Updated when priorities change
completed_work.md         → Updated after every major sprint
open_flaws.md             → Updated when flaws are fixed/reclassified
operational_status.md     → Updated when smoke/demo run status changes
future_roadmap.md         → Updated when roadmap changes
ai_workflow.md            → These rules (rarely changes)
MASTER_CONTEXT.md         → Auto-generated summary of all above
```
