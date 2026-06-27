# Review Cadence

*Version 1.0 — June 2026*

---

## Purpose

The Innovation Engine requires regular review to function. Without cadence, ideas stagnate, priorities drift, and the engine becomes a static document set rather than a living system.

This document defines the four review rhythms that keep the Innovation Engine alive.

---

## Daily Review

**Duration:** 5–10 minutes
**Scope:** Operational only
**Who:** Project lead

### What to Review

- Any operational blockers that need immediate attention
- Any urgent issues from the laptop version (Extended Demo)
- No major architecture or innovation decisions

### What NOT to Review

- New ideas (not enough time for proper review)
- Strategic backlog
- Research questions
- Architecture changes

### Expected Outputs

- Clear picture of today's operational status
- Any blockers identified and assigned
- Decisions about whether to escalate any issue to weekly review

### Decision Rules

- If an operational issue requires a design change, it moves to weekly review — daily review does not make design decisions.
- If an emergency fix is needed, document it in daily review and design the proper fix in weekly review.
- No idea is promoted or demoted during daily review.

---

## Weekly Review

**Duration:** 30–45 minutes
**Scope:** GREEN-lane progress, validation results, observability findings
**Who:** Project lead

### What to Review

| Item | Focus |
|------|-------|
| GREEN-lane implementation progress | Is each implementation on track? Are there blockers? |
| Validation results (from previous week) | Did implemented ideas produce expected outcomes? |
| Terminal cockpit / telemetry findings | What is the operational data telling us? |
| Missed Opportunity Ledger | Are there patterns in rejected or ignored opportunities? |
| Hypothesis and evidence stats | Are hypotheses being created and evaluated? |
| Test results | Are scientific layer tests passing? Any regressions? |
| Any new PROPOSED ideas | Quick triage — does the idea need full review this week? |

### What NOT to Review

- Detailed architecture design (quarterly review)
- Research experiments still in progress
- Strategic backlog items (unless promotion is being considered)

### Expected Outputs

- Updated status of all active GREEN implementations
- Validation evidence reviewed and recorded
- Any GREEN → YELLOW demotions (complexity discovered)
- Any new ideas triaged and assigned to appropriate lane
- Updated `ideas_registry.json` if statuses changed

### Decision Rules

- If a GREEN implementation reveals unexpected complexity, it may be demoted to YELLOW pending redesign.
- If validation evidence is negative, the idea may be moved to FAILED or ARCHIVED.
- If validation evidence is positive, the idea may be promoted to the next state.
- New ideas receive a preliminary lane assignment. Full review happens within 1 week.

---

## Monthly Review

**Duration:** 1–2 hours
**Scope:** Strategic backlog, priority updates, resource allocation
**Who:** Project lead

### What to Review

| Item | Focus |
|------|-------|
| Strategic backlog | Which YELLOW ideas are ready for promotion? |
| Priority map | Are the right items at the right priority? |
| Idea lifecycle status | Are any ideas stuck? Are any becoming zombies? |
| Scarce resources check | Is the project protecting or consuming scarce resources? |
| Innovation Engine itself | Is the Innovation Engine working? What needs improvement? |
| Architecture V2 changes | Any need to update the canonical architecture? |
| YELLOW → GREEN promotions | Which backlog items are now ready? |
| GREEN → YELLOW demotions | Which implement-now items are not working? |

### What NOT to Review

- Detailed research experiments (quarterly review)
- First-principles reassessment (quarterly review)
- Daily operational minutiae

### Expected Outputs

- Updated strategic backlog with promoted/demoted items
- Updated priority map for the next month
- Updated idea lifecycle statuses
- Updated Innovation Engine process if needed
- Updated `ideas_registry.json`

### Decision Rules

- Backlog ideas can be promoted to GREEN if their dependencies are met and the timing is right.
- Backlog ideas can be demoted to RESEARCH LAB if new questions arise.
- Ideas in REVIEWED or CLASSIFIED for more than 1 month without progress must be either promoted or moved to the graveyard.
- At most 2 GREEN ideas can be actively implemented at any time (one-person constraint).
- If scarce resources are being consumed faster than they are being produced, reduce the implementation pace.

---

## Quarterly Review

**Duration:** 3–4 hours
**Scope:** Deep research, architecture, thesis reassessment
**Who:** Project lead

### What to Review

| Item | Focus |
|------|-------|
| Research Lab questions | Any resolved? Any new? Any to be retired? |
| Criterion thesis | Is the central hypothesis holding up? |
| Scarce resources model | Is the model correct? Are all 8 resources being tracked appropriately? |
| One-person maintainability assessment | Is the system still maintainable? Has complexity grown too fast? |
| Architecture V2 | Any changes needed based on accumulated evidence? |
| First-principles documents | Any that need updating based on new evidence? |
| Idea Graveyard | Any ideas that should be reconsidered? |
| Project-wide test health | Are tests still passing? Is coverage sufficient? |
| Overall Innovation Engine effectiveness | Is the engine itself working? What needs to change? |

### What NOT to Review

- Day-to-day implementation status (weekly review covers this)
- Individual idea details (unless they are representative of a pattern)

### Expected Outputs

- Updated research questions with new findings
- Updated thesis documents if evidence justifies changes
- Updated one-person maintainability score
- Updated architecture if needed
- Any graveyard exhumations documented
- Quarterly report summarizing: what was learned, what was built, what was rejected, what changed

### Decision Rules

- Research questions that have been OPEN for 4+ quarters should either be resolved or actively deprioritized.
- If the Criterion thesis is weakened by evidence, the architecture may need to change.
- If the one-person maintainability assessment returns a negative trend, reduce the implementation pace and increase documentation.
- Graveyard ideas can be exhumed only if new evidence directly addresses the original rejection reason.
- The quarterly review may adjust any of the Innovation Engine's own processes based on evidence of what works.

---

## Review Cadence Summary

| Rhythm | Frequency | Duration | Scope | Output |
|--------|-----------|----------|-------|--------|
| **Daily** | Every day | 5–10 min | Operational blockers | Status, escalated issues |
| **Weekly** | Every week | 30–45 min | GREEN progress, validation | Status update, evidence review |
| **Monthly** | Every month | 1–2 hours | Backlog, priorities, resource check | Priority update, promotion/demotion |
| **Quarterly** | Every 3 months | 3–4 hours | Research, architecture, thesis | Quarterly report, document updates |

---

## Calendar Integration

If using a calendar system, set recurring events:

- Daily: 10-minute block (e.g., 09:00)
- Weekly: 45-minute block (e.g., Friday 14:00)
- Monthly: 2-hour block (e.g., First Monday 10:00)
- Quarterly: 4-hour block (e.g., First week of quarter)

---

## What to Do When a Review Is Missed

| Missed | Action |
|--------|--------|
| Daily | Skip. Catch up next day. No cascading impact. |
| Weekly | Reschedule within 2 days. If impossible, merge into next week's review (but do not skip two consecutive weeks). |
| Monthly | Reschedule within 1 week. If the monthly review overlaps with a quarterly review, fold monthly items into quarterly. |
| Quarterly | Do not skip. Reschedule within 2 weeks. The quarterly review is the most important — it is where the project's direction is validated or corrected. |

---
