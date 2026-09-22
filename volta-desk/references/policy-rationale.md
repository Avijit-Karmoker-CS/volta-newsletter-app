# Policy rationale — CLAUDE.md ↔ transcripts

Grounding rule (same as `build-newsletter`): **no CLAUDE.md rule gets a citation here unless it quotes or closely paraphrases a real line in `references/transcripts/`.**

## Transcript status (blocking)

As of this file’s creation, all three transcript files are **placeholders with no interview body**:

| File | Usable dialogue? |
|------|------------------|
| `references/transcripts/bader-interview.md` | No — paste pending |
| `references/transcripts/matt-interview.md` | No — paste pending |
| `references/transcripts/mentor-session.md` | No — paste pending |

Therefore **every rule below is flagged UNCITED**. No quotes or paraphrases were invented from memory, prior chat summaries, or product lore.

When real transcripts are pasted, replace each `UNCITED` block with:

- **Rule:** (verbatim or near-verbatim from CLAUDE.md)
- **Who / what:** quote or close paraphrase + speaker
- **Source:** path + enough context to find the moment (e.g. surrounding turn)

---

## Cadence

### Rule: Default cadence is monthly. That is the spine of this system.

- **Citation:** UNCITED — no line available in `bader-interview.md` (or others).
- **Expected source (once pasted):** Bader rejecting weekly / affirming monthly — do not fill until the transcript has that moment.

### Rule: Never default to, suggest, or nudge toward weekly or biweekly sends.

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Same Bader cadence discussion (including any second rejection of weekly).

### Rule: A flash update is an optional, separate, cheap action for genuinely time-sensitive news only — never a replacement for the monthly issue, and never a prompt to send more often.

- **Citation:** UNCITED — no transcript line available.
- **Note:** This may be a design elaboration of the monthly spine rather than a direct stakeholder quote. Flag for re-check after paste: either cite a real line or demote/remove from CLAUDE.md if unsupported.

---

## Consent gate

### Rule: Nothing enters a draft without `consent_status: approved`.

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Bader on asking founders permission before including their story; and/or Matt on approval before using people’s data.

### Rule: Applies to founder stories and internal Volta data (attendance, meeting notes, program launches, etc.).

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Matt on ownership of internal / person-generated data needing clear approval before use (and Bader on founder stories, if stated separately).

### Rule: Pending, not_requested, declined, or missing consent → exclude. Do not soft-include or “flag for later inside the draft.”

- **Citation:** UNCITED — no transcript line available.
- **Note:** Implementation detail of the consent gate. Needs either an explicit stakeholder line or a clear “derived from [cited consent rule]” once the parent rule is cited — still no invented quote.

---

## Grounding

### Rule: Every claim in a draft must trace to a real file under `inbox/` or `internal-signals/`.

- **Citation:** UNCITED — no transcript line available.
- **Note:** May be system-design / discovery-method (mentor session) rather than a newsletter-content quote. Do not invent; cite mentor-session or interview line after paste, or flag for CLAUDE.md revision.

### Rule: No invented statistics, no paraphrased-into-existence claims, no vague filler where a specific fact should be.

- **Citation:** UNCITED — no transcript line available.

### Rule: If a fact has no source file, omit it.

- **Citation:** UNCITED — no transcript line available.

---

## No time-savings claims

### Rule: Never claim this system saves time (e.g. “cuts prep from X hours to Y minutes”) in generated copy, docs, comments, or skill text.

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Bader stating content volume / prep-time is not his bottleneck (and any note that time-savings claims were previously removed).

---

## Send path

### Rule: Mailchimp is the only thing that emails real subscribers.

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Bader (or ops context in his interview) on sending via Mailchimp.

### Rule: This system drafts and prepares content. It never sends to a live list itself.

- **Citation:** UNCITED — no transcript line available.
- **Note:** Product-boundary statement; needs transcript support or explicit “derived from Mailchimp-only send” once that parent is cited.

### Rule: Do not build or imply an opens/clicks/unsubscribes analytics dashboard — Mailchimp owns that.

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Bader satisfied with Mailchimp’s own analytics (if stated).

---

## Provability

### Rule: Every action must be logged and produce real artifacts (files, status changes, draft outputs).

- **Citation:** UNCITED — no transcript line available.
- **Expected source (once pasted):** Matt on whether input “actually counts” / need for visible proof — only if that line exists after paste.

### Rule: Prefer writing proof to disk over asserting that work was done.

- **Citation:** UNCITED — no transcript line available.
- **Note:** Likely derived from the provability / audit concern; do not invent a Matt quote.

---

## Preamble (also in CLAUDE.md)

### Rule: Operate this folder as Bader’s newsletter desk inside Claude/Cursor. Do not modify or depend on the FastAPI `app/` tree.

- **Citation:** UNCITED — architectural choice for this phase; not expected to appear as interview dialogue unless someone stated “no server / folder in Cursor.” Flag: keep as build constraint or cite if a transcript supports the agent-operated desk.

---

## Action required (maintainer)

1. Paste full transcripts into the three files under `references/transcripts/`.
2. Re-open this document and fill **Rule / Who–what / Source** for each UNCITED item from real lines only.
3. Any CLAUDE.md rule that still cannot be traced after paste should be removed or rewritten — not given a fake rationale.
