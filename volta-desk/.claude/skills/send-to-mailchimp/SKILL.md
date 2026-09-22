---
name: send-to-mailchimp
description: >-
  Hand a Guard-passed Volta desk draft to Mailchimp (demo or live). Use when
  asked to send, finalize for Mailchimp, or push the monthly/flash draft to
  the community list. This is the only Mailchimp touchpoint in volta-desk.
---

# Send to Mailchimp

This skill is the **only** place in volta-desk allowed to talk to Mailchimp. The desk prepares drafts; Mailchimp (or demo mode) is what reaches subscribers.

## Steps

1. **Guard first** — only operate on a draft under `drafts/` that passes the consent Guard (`guard-consent.py --check`). If Guard fails, stop. Do not write to `sent/`. Do not call Mailchimp.
2. **Run the script** from the desk root (or with paths relative to it):

```bash
python .claude/skills/send-to-mailchimp/scripts/send.py drafts/YYYY-MM-<slug>.md
```

3. The script converts markdown to Mailchimp HTML (subscriber body only — strips Sources / Waiting on consent), creates a campaign via the same demo/live rules as the FastAPI desk (`DEMO_MODE` / real `MAILCHIMP_API_KEY`), and on success **moves** the draft from `drafts/` → `sent/`.
4. Confirm console output shows demo or live send result. Append / rely on `logs/` + `logs/activity.log` for the audit trail.

## Rules

- Never email subscribers outside this skill/script.
- Never invent opens/clicks analytics — Mailchimp owns that.
- Never claim time savings.
- Demo mode is the default and works without a real API key.
