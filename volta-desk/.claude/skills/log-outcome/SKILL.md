---
name: log-outcome
description: >-
  Record what happened after an issue was sent — event attendance, sign-ups,
  or other downstream results. Use when Bader reports outcomes for a file in
  sent/, or asks to update outcomes/.
---

# Log outcome

## Steps

1. Given a file in `sent/`, create or update a matching file in `outcomes/` (same basename, or `outcomes/<sent-basename>`).
2. Write a short, specific note of what happened after the send.
3. **No invented numbers** — only record what the user actually tells you happened. If they give no figures, write that no metrics were provided; do not guess attendance, opens, clicks, or sign-ups.
4. Do not pull Mailchimp analytics into this system; Bader uses Mailchimp for that.
5. Write a run record under `logs/`.

## Format

Plain markdown with YAML frontmatter, e.g.:

```markdown
---
sent_file: sent/2026-09-monthly.md
recorded: 2026-09-22
---

Bader reported: …
```
