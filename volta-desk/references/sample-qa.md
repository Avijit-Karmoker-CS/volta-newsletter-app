# Sample Q&A — the folder answering for itself

These three questions were answered by **opening files in this tree and quoting them**, not by recalling a chat.  
Perspective tags: **Rishabh** (product / “show me the wiring”), **Matt** (buyer / “does input count / do I have to trust you”).

Honest gap: `references/transcripts/*.md` are still placeholders, so where a *speaker* line is needed, this doc cites what the folder actually says today (`UNCITED` / `PENDING`) rather than inventing Bader’s or Matt’s words.

---

## 1. “Why does this default to monthly instead of weekly?”

**Likely asker:** Rishabh (design choice / fidelity to discovery)

### Files opened

1. `CLAUDE.md`
2. `references/NOT-BUILT.md`
3. `references/policy-rationale.md`
4. `references/transcripts/bader-interview.md`

### What the folder says

**Enforced rule** — from `CLAUDE.md` (lines 7–9):

> - Default cadence is **monthly**. That is the spine of this system.  
> - Never default to, suggest, or nudge toward weekly or biweekly sends.  
> - A **flash update** is an optional, separate, cheap action for genuinely time-sensitive news only — never a replacement for the monthly issue, and never a prompt to send more often.

**Deliberate omission** — from `references/NOT-BUILT.md` (lines 11–20):

> ## 1. Weekly (or any more-frequent-by-default) cadence  
> …  
> **Why:** Bader rejected weekly twice — including under a generous hypothetical with unlimited content — citing subscriber fatigue and Volta’s monthly event structure, not his own prep time.  
> **Source:** `references/transcripts/bader-interview.md`  
> **Verbatim line:** PENDING — paste transcript, then cite the two weekly-rejection moments here.

**Citation honesty** — from `references/policy-rationale.md` (lines 27–30):

> ### Rule: Default cadence is monthly. That is the spine of this system.  
> - **Citation:** UNCITED — no line available in `bader-interview.md` (or others).  
> - **Expected source (once pasted):** Bader rejecting weekly / affirming monthly — do not fill until the transcript has that moment.

**Transcript file as opened** — from `references/transcripts/bader-interview.md` (lines 1–3):

> # Bader interview — PLACEHOLDER (raw transcript not available)  
> **STATUS:** Raw transcript text was **not** present in this repository or in this agent session.  
> Do **not** treat anything below as Bader’s words.

### Answer in one breath

The system defaults to monthly because `CLAUDE.md` hard-codes it and `NOT-BUILT.md` records weekly-by-default as rejected. The *interview* line that should sit under that decision is not in the folder yet — `policy-rationale.md` and `bader-interview.md` say so out loud. That is the folder being checkable, not a sales answer.

---

## 2. “How do I know my suggestion won’t just disappear?”

**Likely asker:** Matt (leadership tip / “does my input actually count”)

### Files opened

1. `references/for-matt.md`
2. `sent/2026-09-monthly.md`
3. `logs/activity.log`
4. `CLAUDE.md` (provability)

### What the folder says

**Stated buyer concern** — from `references/for-matt.md` (lines 13, 19):

> …leaving a trail so a tip from leadership isn’t lost in a chat.  
> …  
> The risk it is meant to cut is the opposite problem: someone on the team flags something important, and it quietly never shows up in an issue, with no record of why.

**A tip that made the issue** — from `sent/2026-09-monthly.md` (Sources, lines 47–48):

> - `inbox/2026-09-22-matt-bridge-priority.md` — approved leadership priority to keep Bridge launch visible  
> - `inbox/2026-09-20-rishabh-founder-pilot.md` — approved founder pilot win (no company/dollars)

**A tip that did not vanish when blocked** — from `sent/2026-09-monthly.md` (Waiting on consent, lines 50–52):

> ## Waiting on consent  
> - `internal-signals/2026-09-15-meeting-residency-quote.md` — `not_requested` (founder quote; internal until founder approves public use)

**Audit trail of Matt’s Bridge tip moving through consent** — from `logs/activity.log` (line 2):

> `2026-09-22T13:39:38-03:00 | skill=request-consent | files=inbox/2026-09-22-matt-bridge-priority.md | Bridge tip not_requested→pending→approved`

**And of a build that kept waiting items visible** — from `logs/activity.log` (line 8):

> `2026-09-22T13:45:10-03:00 | skill=build-newsletter | files=drafts/2026-09-monthly.md | Proof monthly build: 4 approved in, residency quote waiting`

**Provability rule** — from `CLAUDE.md` (lines 35–36):

> - Every action must be logged and produce real artifacts (files, status changes, draft outputs).  
> - Prefer writing proof to disk over asserting that work was done.

### Answer in one breath

A suggestion becomes a file; if it isn’t in the letter, it still shows under **Waiting on consent** or in `logs/activity.log`. Matt’s Bridge tip is on the Sources list of `sent/2026-09-monthly.md` and in the activity log as `not_requested→pending→approved`. Disappearing silently would violate how this folder is written.

---

## 3. “What stops this from becoming another thing I have to trust blindly?”

**Likely asker:** Rishabh (verify the mechanism) — also what Matt needs for spend confidence

### Files opened

1. `.claude/hooks/guard-consent.py`
2. `PROOF.md` (Guard section)
3. `logs/activity.log`
4. `references/compliance-note.md`
5. `references/for-matt.md` (proof pointer)

### What the folder says

**Structural block (not a promise)** — from `.claude/hooks/guard-consent.py` (lines 68–71):

> if status != "approved":  
>     errors.append(  
>         f"Guard blocked: '{rel}' has consent_status='{status or 'missing'}' "  
>         f"(must be 'approved' before anything is treated as ready for Mailchimp)."  
>     )

**That block actually ran** — from `PROOF.md` (lines 238–241):

> ```bash  
> $ python3 volta-desk/.claude/hooks/guard-consent.py --check /tmp/volta-proof-bad-sent.md  
> Guard blocked: 'internal-signals/2026-09-15-meeting-residency-quote.md' has consent_status='not_requested' (must be 'approved' before anything is treated as ready for Mailchimp).  
> guard_exit=2  
> ```

**Logged in the audit trail** — from `logs/activity.log` (line 9):

> `2026-09-22T13:45:11-03:00 | skill=build-newsletter | files=sent/ (blocked) | Guard blocked finalize referencing not_requested residency quote`

**CASL / subscriber trust** — from `references/compliance-note.md` (full body):

> This desk never stores, processes, or sends to a real subscriber’s email address. The audience list and every live send stay in Mailchimp alone; volta-desk only produces a reviewed draft (and, when configured, hands campaign content to Mailchimp’s API without keeping a local copy of the list). Volta’s existing CASL posture is unchanged, because nothing in this system touches subscriber data.

**Where to re-check anytime** — from `references/for-matt.md` (lines 25–27):

> A full month was run end to end with real files and console output in `PROOF.md`. Ongoing runs leave an audit trail in `logs/activity.log` — which skill ran, what it touched, what happened — so you can check whether input actually counted without taking anyone’s word for it.

### Answer in one breath

You don’t have to trust a pitch: open `PROOF.md` and `logs/activity.log` for a real Guard deny (`exit 2`), open `guard-consent.py` for the code that emits it, open `compliance-note.md` for subscriber-data scope, and open `policy-rationale.md` / transcripts for whether a rule is actually cited yet. Blind trust is what this folder is built to make unnecessary.

---

## How to re-run this check

1. Ask the same three questions against a fresh checkout.  
2. Prefer `Read` / open of the paths named above over chat memory.  
3. After interview transcripts are pasted, Q1’s second click should move from `PENDING` / `UNCITED` to a real `Bader:` line in `references/transcripts/bader-interview.md` — update `policy-rationale.md` and this file when that happens.
