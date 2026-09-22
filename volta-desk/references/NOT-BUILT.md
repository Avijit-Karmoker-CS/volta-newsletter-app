# Not built — deliberate restraint

This list is **not a backlog**. These ideas were considered and **explicitly left out** so the desk follows discovery evidence, not “we could build it.”

That matches Matt’s coaching (once the mentor / Matt transcripts are filled): don’t add features until the interview shows a gap.

**Transcript status:** `bader-interview.md`, `matt-interview.md`, and `mentor-session.md` are still placeholders with no dialogue body. Items below name the intended source file and the reason as established in product discovery. **Verbatim speaker lines are marked PENDING** — do not invent quotes. After paste, replace each PENDING with a real line from that file (same grounding rule as `policy-rationale.md`).

---

## 1. Weekly (or any more-frequent-by-default) cadence

**Left out:** Defaulting to weekly or biweekly sends, or any UI/skill nudge that pushes “send more often.”

**What exists instead:** Monthly as the spine (`CLAUDE.md` cadence). An optional, manual, opt-in **flash update** for genuinely time-sensitive news only — never a replacement for the monthly issue.

**Why:** Bader rejected weekly twice — including under a generous hypothetical with unlimited content — citing subscriber fatigue and Volta’s monthly event structure, not his own prep time.

**Source:** `references/transcripts/bader-interview.md`  
**Verbatim line:** PENDING — paste transcript, then cite the two weekly-rejection moments here.

---

## 2. Built-in analytics dashboard (opens / clicks / unsubscribes)

**Left out:** Any opens/clicks/unsubscribe dashboard or analytics product inside volta-desk (or a parallel “newsletter metrics” surface).

**What exists instead:** Outcome notes Bader actually reports (`outcomes/`), after a send. Mailchimp remains the analytics system of record.

**Why:** Bader already uses Mailchimp’s own analytics and is satisfied with it. Building a second dashboard would be duplicative and out of scope.

**Source:** `references/transcripts/bader-interview.md`  
**Verbatim line:** PENDING — paste transcript, then cite the Mailchimp-analytics satisfaction moment here.

---

## 3. Direct Mailchimp replacement (sending + audience management)

**Left out:** Replacing Mailchimp for live list send, audience/list management, or becoming the ESP.

**What exists instead:** `send-to-mailchimp` prepares a campaign via Mailchimp’s API (or demo mode). The desk drafts and gates content; Mailchimp is the only path that emails real subscribers.

**Why:** Matt was explicit that Mailchimp stays unless there is a real reason to switch. No such reason was established for this system.

**Source:** `references/transcripts/matt-interview.md`  
**Verbatim line:** PENDING — paste transcript, then cite the “Mailchimp stays” moment here.

---

## 4. Automated cadence experiments

**Left out:** Automated A/B or scheduled experiments that vary send frequency by default, or a “test weekly vs monthly” feature shipped without a named hypothesis.

**What exists instead:** Fixed monthly default. Frequency changes only by deliberate configuration / human decision — not an always-on experiment engine.

**Why:** Matt raised the idea of testing frequency by hypothesis, but also stated the restraint rule: don’t add features until the interview shows a gap. There is no specific frequency hypothesis to test yet, so this stays deliberately unbuilt.

**Sources:**  
- Idea / hypothesis framing: `references/transcripts/matt-interview.md`  
- Restraint / don’t-build-until-gap: `references/transcripts/mentor-session.md` (discovery framework coaching) and/or `matt-interview.md` once pasted  

**Verbatim lines:** PENDING — paste transcripts, then cite (1) the cadence-experiment idea and (2) the “don’t add features until there’s a gap” rule here.

---

## How to use this file

- Reviewers: if something “missing” is on this list, that is intentional.
- Builders: do not implement these without a new transcript-backed gap and an update to this file + `policy-rationale.md`.
- After transcripts are pasted: fill every PENDING with a real quote or close paraphrase and leave the rest of the rationale intact.
