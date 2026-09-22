# Volta Desk — monthly proof run

**When:** 2026-09-22  
**Operator role:** Bader’s monthly issue, end to end  
**Mode:** `DEMO_MODE=true` (no live email)

This document pastes **real file contents and console output** from one complete run. It is not a description of what would happen.

---

## 1. Starting state — `inbox/` and `internal-signals/`

### `ls volta-desk/inbox/`

```
2026-09-18-laura-ai-showcase-recap.md
2026-09-20-rishabh-founder-pilot.md
2026-09-22-matt-bridge-priority.md
```

### `inbox/2026-09-18-laura-ai-showcase-recap.md`

```markdown
---
author: Laura
consent_status: approved
date: 2026-09-18
tags: [events, community]
---
Flag the AI Showcase recap for this month's issue — strong turnout, good for community visibility. Keep it short; link to the event page if we have one.
```

### `inbox/2026-09-20-rishabh-founder-pilot.md` (before consent)

```markdown
---
author: Rishabh
consent_status: pending
date: 2026-09-20
tags: [founder, wins]
consent_contact: jane@example-startup.ca
---
Founder story lead: a resident closed a first paid pilot with a local enterprise. Do not name the company or dollar amount until Jane confirms wording. Ask her before any draft includes this.
```

### `inbox/2026-09-22-matt-bridge-priority.md`

```markdown
---
author: Matt
consent_status: approved
date: 2026-09-22
tags: [programs, bridge, priority]
---
Keep the Bridge program launch visible in this issue. Leadership priority — public wording still needs a yes before we describe cohort details.

## Consent log

- 2026-09-22 — Requested from Matt (leadership / program owner). Status set to `pending`. Models Bader’s hand-ask as a tracked desk action.
- 2026-09-22 — Response recorded: **approved**. Matt confirmed Bridge launch may appear in the monthly issue; still no cohort details beyond what this file states.
```

### `ls volta-desk/internal-signals/`

```
2026-09-12-attendance-ai-showcase.md
2026-09-15-meeting-residency-quote.md
```

### `internal-signals/2026-09-12-attendance-ai-showcase.md`

```markdown
---
author: Amy
consent_status: approved
date: 2026-09-12
kind: attendance
event: AI Showcase
source_note: Event ops tally · demo seed
---
AI Showcase attendance (internal): 47 registered, 41 checked in. Use only the checked-in figure if this appears in the letter. No individual names without separate consent.
```

### `internal-signals/2026-09-15-meeting-residency-quote.md` (left unapproved on purpose)

```markdown
---
author: Laura
consent_status: not_requested
date: 2026-09-15
kind: meeting_note
topic: residency check-in
source_note: Call notes · demo seed
---
Residency check-in note: one founder described the space as “where we finally stopped building in isolation.” Quote is internal until the founder approves public use. Do not attribute by name without consent.
```

**Consent snapshot at start of this proof month**

| File | consent_status |
|------|----------------|
| Laura AI Showcase tip | `approved` |
| Rishabh founder pilot | `pending` |
| Matt Bridge priority | `approved` |
| Amy attendance signal | `approved` |
| Residency quote signal | `not_requested` ← left this way for Guard proof |

---

## 2. `request-consent` — approve the pending item

Skill: `request-consent`  
Target: `inbox/2026-09-20-rishabh-founder-pilot.md`  
Action: `pending` → `approved` (Jane confirmed; still no company/dollars)

### File after request-consent

```markdown
---
author: Rishabh
consent_status: approved
date: 2026-09-20
tags: [founder, wins]
consent_contact: jane@example-startup.ca
---
Founder story lead: a resident closed a first paid pilot with a local enterprise. Do not name the company or dollar amount until Jane confirms wording. Ask her before any draft includes this.

## Consent log

- 2026-09-22 — Request already open (`pending`) to Jane at jane@example-startup.ca.
- 2026-09-22 — Response recorded: **approved**. Jane confirmed the pilot win may appear. Still no company name or dollar amount in any draft.
```

### Journal line written

```
2026-09-22T13:45:00-03:00 | skill=request-consent | files=inbox/2026-09-20-rishabh-founder-pilot.md | pending→approved (Jane); residency quote left not_requested for Guard proof
```

Residency quote remains `not_requested` (still on disk as in step 1).

---

## 3. `build-newsletter` — real generated draft

Skill: `build-newsletter` (monthly)  
Output path at generation time: `drafts/2026-09-monthly.md`

### Draft as generated (before send)

```markdown
---
type: monthly
period: 2026-09
built: 2026-09-22
skill: build-newsletter
proof_run: true
---

# Volta newsletter — Month of September 2026

## Community

### AI Showcase recap

Volta’s AI Showcase drew strong community turnout. **41 people checked in.**

*(Sources: Laura’s staff tip for a short recap; Amy’s attendance tally for the checked-in figure only.)*

## Programs

### Bridge launch

Keep the Bridge program launch visible this month. Volta Bridge is live as a leadership priority for this issue.

*(Source: Matt’s approved tip. No cohort details — none are stated in the source file.)*

## Member wins

### First paid pilot

A Volta resident closed a first paid pilot with a local enterprise.

*(Source: Rishabh’s tip, approved by Jane. No company name and no dollar amount — the source forbids both until further notice.)*

---

## Sources

- `inbox/2026-09-18-laura-ai-showcase-recap.md` — staff tip to include a short AI Showcase recap
- `internal-signals/2026-09-12-attendance-ai-showcase.md` — checked-in count (41)
- `inbox/2026-09-22-matt-bridge-priority.md` — approved leadership priority to keep Bridge launch visible
- `inbox/2026-09-20-rishabh-founder-pilot.md` — approved founder pilot win (no company/dollars)

## Waiting on consent

- `internal-signals/2026-09-15-meeting-residency-quote.md` — `not_requested` (founder quote; internal until founder approves public use)
```

### Journal line written

```
2026-09-22T13:45:10-03:00 | skill=build-newsletter | files=drafts/2026-09-monthly.md | Proof monthly build: 4 approved in, residency quote waiting
```

---

## 4. Guard Hook — prove it blocks an unapproved item

Left unapproved: `internal-signals/2026-09-15-meeting-residency-quote.md` (`not_requested`).

Deliberately tried to finalize a draft that **references that quote as a Source** (as if ready for Mailchimp).

### Bad payload used for the test

```markdown
---
type: monthly
period: 2026-09
---

# Bad finalize — includes unapproved quote

A founder described the space as “where we finally stopped building in isolation.”

## Sources

- `internal-signals/2026-09-15-meeting-residency-quote.md`
- `inbox/2026-09-18-laura-ai-showcase-recap.md`

## Waiting on consent

(empty — wrongly treated unapproved quote as ready)
```

### Command + real stderr / exit

```bash
$ python3 volta-desk/.claude/hooks/guard-consent.py --check /tmp/volta-proof-bad-sent.md
Guard blocked: 'internal-signals/2026-09-15-meeting-residency-quote.md' has consent_status='not_requested' (must be 'approved' before anything is treated as ready for Mailchimp).
guard_exit=2
```

### Simulated PreToolUse Write → `sent/` (same block)

```
Guard blocked: 'internal-signals/2026-09-15-meeting-residency-quote.md' has consent_status='not_requested' (must be 'approved' before anything is treated as ready for Mailchimp).
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Guard blocked: 'internal-signals/2026-09-15-meeting-residency-quote.md' has consent_status='not_requested' (must be 'approved' before anything is treated as ready for Mailchimp)."}}
pretool_exit=2
```

### Same Guard on the real monthly draft (Sources are all approved)

```bash
$ python3 volta-desk/.claude/hooks/guard-consent.py --check volta-desk/drafts/2026-09-monthly.md
OK: all referenced sources are consent-approved.
good_exit=0
```

---

## 5. `send-to-mailchimp` — demo mode console output

```bash
$ DEMO_MODE=true MAILCHIMP_API_KEY=DEMO_MAILCHIMP_KEY \
  python3 volta-desk/.claude/skills/send-to-mailchimp/scripts/send.py \
  volta-desk/drafts/2026-09-monthly.md
```

### Real console output

```
Draft: /Users/avijit.karmoker/Desktop/My MacBook/Volta/volta-newsletter-app/volta-desk/drafts/2026-09-monthly.md
DEMO_MODE effective: True
Guard: passed (all referenced sources consent_status=approved)
Subject: Volta newsletter — Month of September 2026
HTML bytes: 1228
Calling Mailchimp create_campaign_and_send …

======== MAILCHIMP SEND RESULT ========
demo:             True
campaign_id:      demo_6d5eb68854
status:           sent
sent:             True
recipient_count:  12
from_name:        Volta
reply_to:         hello@voltaeffect.com
created_at:       2026-09-22T16:45:17Z
html_bytes:       1228
message:          Demo Mailchimp send complete — no live email left the building. Swap DEMO keys for a real MAILCHIMP_API_KEY when ready.
moved:            drafts/2026-09-monthly.md → sent/2026-09-monthly.md
log:              logs/2026-09-22-send-to-mailchimp-2026-09-monthly.md
=======================================
send_exit=0
```

`drafts/` is empty afterward (only `.gitkeep`).

---

## 6. Final state — `sent/`, `outcomes/`, `logs/activity.log`

### `ls volta-desk/sent/`

```
.gitkeep
2026-09-monthly.md
```

### `sent/2026-09-monthly.md` (full file after send)

```markdown
---
type: monthly
period: 2026-09
built: 2026-09-22
skill: build-newsletter
proof_run: true
sent_at: 2026-09-22T16:45:17Z
mailchimp_campaign_id: demo_6d5eb68854
mailchimp_demo: true
mailchimp_status: sent
mailchimp_recipient_count: 12
skill: send-to-mailchimp
---

# Volta newsletter — Month of September 2026

## Community

### AI Showcase recap

Volta’s AI Showcase drew strong community turnout. **41 people checked in.**

*(Sources: Laura’s staff tip for a short recap; Amy’s attendance tally for the checked-in figure only.)*

## Programs

### Bridge launch

Keep the Bridge program launch visible this month. Volta Bridge is live as a leadership priority for this issue.

*(Source: Matt’s approved tip. No cohort details — none are stated in the source file.)*

## Member wins

### First paid pilot

A Volta resident closed a first paid pilot with a local enterprise.

*(Source: Rishabh’s tip, approved by Jane. No company name and no dollar amount — the source forbids both until further notice.)*

---

## Sources

- `inbox/2026-09-18-laura-ai-showcase-recap.md` — staff tip to include a short AI Showcase recap
- `internal-signals/2026-09-12-attendance-ai-showcase.md` — checked-in count (41)
- `inbox/2026-09-22-matt-bridge-priority.md` — approved leadership priority to keep Bridge launch visible
- `inbox/2026-09-20-rishabh-founder-pilot.md` — approved founder pilot win (no company/dollars)

## Waiting on consent

- `internal-signals/2026-09-15-meeting-residency-quote.md` — `not_requested` (founder quote; internal until founder approves public use)
```

### `log-outcome` → `outcomes/2026-09-monthly.md`

```markdown
---
sent_file: sent/2026-09-monthly.md
recorded: 2026-09-22
skill: log-outcome
proof_run: true
---

Bader (proof walkthrough): demo Mailchimp send completed for the September issue. No post-send attendance or sign-up figures were provided — none recorded.
```

### `logs/activity.log` (full file)

```
2026-09-22T13:39:38-03:00 | skill=build-newsletter | files=drafts/2026-09-monthly.md | Monthly rebuild after Bridge consent approved
2026-09-22T13:39:38-03:00 | skill=request-consent | files=inbox/2026-09-22-matt-bridge-priority.md | Bridge tip not_requested→pending→approved
2026-09-22T13:39:39-03:00 | skill=log-outcome | files=outcomes/2026-09-monthly.md | Outcome note recorded; no metrics invented
2026-09-22T13:39:39-03:00 | skill=build-newsletter | files=sent/2026-09-monthly.md | Finalize blocked by Guard: pending founder pilot referenced
2026-09-22T13:39:39-03:00 | skill=build-newsletter | files=/Users/avijit.karmoker/Desktop/My MacBook/Volta/volta-newsletter-app/volta-desk/drafts/2026-09-monthly.md | Write wrote 2026-09-monthly.md
2026-09-22T13:41:53-03:00 | skill=send-to-mailchimp | files=sent/2026-09-monthly.md,logs/2026-09-22-send-to-mailchimp-2026-09-monthly.md | Demo Mailchimp send complete — no live email left the building. Swap DEMO keys for a real MAILCHIMP_API_KEY when ready.
2026-09-22T13:45:00-03:00 | skill=request-consent | files=inbox/2026-09-20-rishabh-founder-pilot.md | pending→approved (Jane); residency quote left not_requested for Guard proof
2026-09-22T13:45:10-03:00 | skill=build-newsletter | files=drafts/2026-09-monthly.md | Proof monthly build: 4 approved in, residency quote waiting
2026-09-22T13:45:11-03:00 | skill=build-newsletter | files=sent/ (blocked) | Guard blocked finalize referencing not_requested residency quote
2026-09-22T13:45:17-03:00 | skill=send-to-mailchimp | files=sent/2026-09-monthly.md,logs/2026-09-22-send-to-mailchimp-2026-09-monthly.md | Demo Mailchimp send complete — no live email left the building. Swap DEMO keys for a real MAILCHIMP_API_KEY when ready.
2026-09-22T13:45:17-03:00 | skill=log-outcome | files=outcomes/2026-09-monthly.md | Proof: demo send confirmed; no post-send figures provided
```

Proof-month lines are the last five entries (`13:45:00`–`13:45:17`).

---

## What this run proved on disk

1. Pending founder tip was approved via `request-consent` with a consent log.
2. `build-newsletter` included only `approved` sources and listed the residency quote under **Waiting on consent**.
3. Guard **blocked** (`exit 2`) a finalize that cited the still-`not_requested` residency quote.
4. Guard **passed** the real draft; `send-to-mailchimp` completed a **demo** campaign (`demo_6d5eb68854`) and moved the file to `sent/`.
5. `outcomes/` and `logs/activity.log` hold the audit trail without invented metrics.
