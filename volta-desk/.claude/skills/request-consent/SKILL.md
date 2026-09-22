---
name: request-consent
description: >-
  Request or record yes/no consent for a story or internal signal before it
  can enter a draft. Use when an inbox/ or internal-signals/ item needs
  permission from the person it is about, or when that person has replied
  approved/declined.
---

# Request consent

Model what Bader already does by hand — asking permission — as an explicit, trackable file action. Never invent a reply.

## Request (ask)

Given a file in `inbox/` or `internal-signals/`:

1. Set frontmatter `consent_status` to `pending`.
2. Append a short note under the body (or a `## Consent log` section) recording that a request was made: **who** was asked, **when** (ISO date), and optionally how (e.g. Slack/email) if the user said so.
3. Do not change the story body facts.
4. Write a run record under `logs/`.

If status is already `approved` or `declined`, do not reset to `pending` unless the user explicitly asks to re-request.

## Record response

When the user reports a reply:

1. Set `consent_status` to `approved` or `declined` as stated.
2. Append a consent-log note: who responded, when, and the decision. No paraphrase that softens a decline into a maybe.
3. Write a run record under `logs/`.

## Rules

- Consent is a hard gate for `build-newsletter`. This skill only updates status and the audit note — it does not draft newsletter copy.
- Never mark `approved` or `declined` without the user (or a clear recorded reply they provide) saying so.
