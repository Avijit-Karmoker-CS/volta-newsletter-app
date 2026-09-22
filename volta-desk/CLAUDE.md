# Volta Desk — always-on rules

Operate this folder as Bader’s newsletter desk inside Claude/Cursor. Do not modify or depend on the FastAPI `app/` tree. Follow these rules on every action.

## Cadence

- Default cadence is **monthly**. That is the spine of this system.
- Never default to, suggest, or nudge toward weekly or biweekly sends.
- A **flash update** is an optional, separate, cheap action for genuinely time-sensitive news only — never a replacement for the monthly issue, and never a prompt to send more often.

## Consent gate

- Nothing enters a draft without `consent_status: approved`.
- Applies to founder stories and internal Volta data (attendance, meeting notes, program launches, etc.).
- Pending, not_requested, declined, or missing consent → exclude. Do not soft-include or “flag for later inside the draft.”

## Grounding

- Every claim in a draft must trace to a real file under `inbox/` or `internal-signals/`.
- No invented statistics, no paraphrased-into-existence claims, no vague filler where a specific fact should be.
- If a fact has no source file, omit it.

## No time-savings claims

- Never claim this system saves time (e.g. “cuts prep from X hours to Y minutes”) in generated copy, docs, comments, or skill text.

## Send path

- Mailchimp is the only thing that emails real subscribers.
- This system drafts and prepares content. It never sends to a live list itself.
- Do not build or imply an opens/clicks/unsubscribes analytics dashboard — Mailchimp owns that.

## Provability

- Every action must be logged and produce real artifacts (files, status changes, draft outputs).
- Prefer writing proof to disk over asserting that work was done.

Policy rationale (who said what): `references/policy-rationale.md`.
