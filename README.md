# Volta Newsletter App

Internal **desktop** app for Volta’s weekly community newsletter. Built for Bader (Monday morning or anytime), with access for Matt, Rishabh, Laura, Amy, and other staff.

This is **not** a web frontend. It is a native Python desktop app (CustomTkinter) that sits **alongside Mailchimp** — lists, unsubscribe, and send stay in the Mailchimp account Volta already uses.

## What it does

1. **Default generate** — one click builds the popular template from community signals + open staff recommendations.
2. **Customize** — Bader enters a plan/prompt; the app researches builder/community interest signals and folds in staff recommendations.
3. **Staff recommendations** — any logged-in staff member can add what should go in the letter; Bader sees them when generating.
4. **Review** — preview HTML before anything goes out.
5. **Email to community** — one button loads the Mailchimp audience, lets Bader confirm recipients, then creates/sends the campaign in Mailchimp.

## Quick start

```bash
cd volta-newsletter-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Demo staff PINs (change for production)

| Person   | Username | PIN  | Role        |
|----------|----------|------|-------------|
| Bader    | bader    | 1111 | editor      |
| Matt     | matt     | 2222 | admin       |
| Rishabh  | rishabh  | 3333 | contributor |
| Laura    | laura    | 4444 | contributor |
| Amy      | amy      | 5555 | contributor |

## Mailchimp (.env)

Use the **same** Mailchimp account / audience Volta already runs:

```
MAILCHIMP_API_KEY=...
MAILCHIMP_SERVER_PREFIX=usX
MAILCHIMP_AUDIENCE_ID=...
MAILCHIMP_FROM_NAME=Volta
MAILCHIMP_REPLY_TO=hello@voltaeffect.com
```

Without keys, the app runs in **demo mode** (local draft + sample community list). No send happens until Mailchimp is configured.

## Optional AI research

```
OPENAI_API_KEY=...
```

If unset, customize mode still works with local/community heuristics and Eventbrite reachability checks.

## Flow (Bader)

1. Sign in Monday morning (or anytime).
2. Either **Build from template** or **Customize newsletter**.
3. Staff may already have left recommendations in the inbox.
4. **Review newsletter** → edit HTML if needed → **Email to community**.
5. Campaign is created and sent through Mailchimp.

## Project layout

```
main.py                 # launch desktop app
app/ui/                 # desktop screens
app/services/           # newsletter, research, Mailchimp, storage
data/local/             # drafts + recommendations (gitignored)
```

## License

Internal Volta use.
