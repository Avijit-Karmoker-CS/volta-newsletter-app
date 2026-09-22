---
name: build-newsletter
description: >-
  Draft or build this month's Volta newsletter issue, or a flash update.
  Use when asked to write, build, draft, or assemble the monthly letter or
  an optional flash update from inbox/ and internal-signals/.
---

# Build newsletter

Prepare a draft for Bader. Mailchimp sends; this skill only writes files under `drafts/`.

## 1. Before starting — gather context

1. **Monthly or flash?** Default assumption: **monthly**, unless the user clearly signals a flash update.
2. **Read every file** in `inbox/` and `internal-signals/`. For each, check the `consent_status` frontmatter field.
3. **Eligibility**
   - Only items with `consent_status: approved` may be drafted.
   - Items that are `not_requested` or `pending` must be listed separately as **waiting on consent** — never silently dropped, and never included.
   - Treat `declined` or missing consent the same as ineligible; list them under waiting/excluded with the reason.

## 2. Grounding (structural)

Every fact or claim written into the draft must cite which specific file in `inbox/` or `internal-signals/` it came from.

If a claim cannot be traced to a real source file, do not write it — no invented details, no vague filler standing in for a specific fact.

## 3. Prohibitions

Never write or imply a time-savings claim (hours saved, minutes saved) anywhere in the draft or its surrounding copy.

## 4. Output — monthly issue

Write plain markdown to `drafts/YYYY-MM-<slug>.md` — no HTML, no styling; readable content Bader can review directly.

Required sections at the bottom of the draft:

- **Sources** — every source file used
- **Waiting on consent** — anything excluded and why

Also append a short run record under `logs/` (skill name, timestamp, output path, eligible vs waiting counts).

## 5. Output — flash update

Same consent and grounding rules apply.

Write a short **single-item** draft, clearly labeled as a flash update and separate from the monthly issue (e.g. `drafts/YYYY-MM-DD-flash-<slug>.md`).

Include the same **Sources** and **Waiting on consent** sections. Log the run under `logs/`.
