# For Matt — short buyer brief

Phone-length answers to the economic questions. Not a pitch.

## What does this cost to run?

Nothing beyond Claude or Cursor, which Bader already uses. No hosting bill, no new SaaS subscription, no server to keep alive. The desk is a folder on disk plus the tools he already opens for work.

## What does it replace?

Nothing that already sends email. Mailchimp still sends to the community.

What it takes over is the messy middle: deciding what is allowed in this month’s letter, getting a clear yes before someone’s story or internal note is used, and leaving a trail so a tip from leadership isn’t lost in a chat.

## What risk does it introduce?

None to subscriber data. This system never holds or emails the audience list — see `references/compliance-note.md`. Mailchimp stays the only place that knows subscribers and the only thing that sends.

The risk it is meant to cut is the opposite problem: someone on the team flags something important, and it quietly never shows up in an issue, with no record of why.

## What did we deliberately not build, and why?

Things that sounded useful but the interviews said not to ship yet — weekly-by-default sends, a second analytics dashboard, replacing Mailchimp, automated frequency experiments. Reasons are in `references/NOT-BUILT.md`.

## Where’s the proof this isn’t just a pitch?

A full month was run end to end with real files and console output in `PROOF.md`. Ongoing runs leave an audit trail in `logs/activity.log` — which skill ran, what it touched, what happened — so you can check whether input actually counted without taking anyone’s word for it.
