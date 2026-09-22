# Volta Newsletter App

Internal newsletter desk for **Bader and staff** — phone and desktop in a browser.

Mailchimp sends the newsletter. It doesn't know what should go in it, and it can't ask a founder for permission or catch a story sitting in your team's own meeting notes. This app decides what goes in, tracks who suggested it, and gets permission to use it — without the manual chasing. Bader still hits send in Mailchimp exactly like today. Leadership doesn't log into anything new — they just get asked, and you can finally see whether what you flagged made it in.

## Quick start (always-on desk)

Open the fixed desk URL (set after deploy — see **Hosting** below):

**Desk:** https://volta-newsletter.fly.dev

Login: **Bader / 1111** (Matt `2222`, Laura `4444`, …)

Cadence defaults to **monthly** (`NEWSLETTER_CADENCE=monthly`). Change only deliberately — there is no nudge to send weekly.

### Demo flow

1. **Build now** or **Customize**
2. **Review & send**
3. Keep community members checked
4. Tap **Email to community** (demo send — no live email)
5. **Send history** to confirm

Staff tip without logging in: `/suggest-newsletter` in Slack, open **/suggest**, or `POST /ingest/email`.

## Hosting (persistent service)

The desk is meant to run on Fly.io / Render / Railway — not on someone's laptop — so it stays up when the machine sleeps.

This repo includes:

- `Dockerfile` — runs `uvicorn` on `$PORT`
- `fly.toml` — Fly.io app + **persistent volume** at `/data`
- `render.yaml` — Render blueprint with a disk at `/data`

### Persistence warning

Recommendations, drafts, sends, and consent live as JSON under `VOLTA_DATA_DIR` (default `./data/local` locally, `/data` in the container).

**Most free tiers wipe the container filesystem on every redeploy or restart.** Without a mounted volume:

- staff tips and founder consent status are lost
- send history disappears

On Fly, `fly.toml` mounts volume `volta_data` → `/data`. On Render, attach the disk in `render.yaml` (may require a paid plan — if the host has no disk, treat the desk as demo-only and expect data loss).

### Secrets (host env — never commit)

Set these in the host dashboard / `fly secrets set` — not in git:

| Variable | Notes |
| --- | --- |
| `VOLTA_SESSION_SECRET` | **Required** on any public URL. `openssl rand -hex 32` |
| `MAILCHIMP_API_KEY` | `DEMO_MAILCHIMP_KEY` for demo, or a real key |
| `DEMO_MODE` | `true` until live Mailchimp |
| `OPENAI_API_KEY` | optional |
| `EMAIL_IN_TOKEN` | optional gate for `/ingest/email` |
| `SLACK_SIGNING_SECRET` | required for `/slack/suggest` + `/slack/interactive` |
| `SLACK_BOT_TOKEN` | Bot User OAuth Token (`xoxb-…`) for consent DMs (`chat:write`, `im:write`) |
| `SLACK_WEBHOOK_URL` | optional Incoming Webhook for `#newsletter-desk` (draft + send pings) |
| `VOLTA_PUBLIC_URL` | optional public desk URL for Slack links (defaults to Fly app URL) |

The app **refuses to start** on Fly/Render/Railway if `VOLTA_SESSION_SECRET` is missing or still the local demo default.

### Deploy on Fly.io

```bash
fly auth login
fly apps create volta-newsletter
fly volumes create volta_data --region yyz --size 1
fly secrets set VOLTA_SESSION_SECRET="$(openssl rand -hex 32)" \
  DEMO_MODE=true MAILCHIMP_API_KEY=DEMO_MAILCHIMP_KEY
fly deploy
```

Then put the printed `https://….fly.dev` URL at the top of this README (and share it with Bader).

Live desk (already deployed): **https://volta-newsletter.fly.dev**

## Local development (optional)

Only for hacking on the code — not how Bader should use the desk day to day.

```bash
cd volta-newsletter-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # demo Mailchimp; leave VOLTA_SESSION_SECRET blank locally
python main.py
```

- Desktop: http://127.0.0.1:8000
- Phone (same Wi‑Fi): URL printed in the terminal

Optional terminal UI: `python main.py --tui`

## Email-in (no login)

```bash
curl -s -X POST https://volta-newsletter.fly.dev/ingest/email \
  -H 'Content-Type: application/json' \
  -d '{"from":"laura@voltaeffect.com","subject":"Member win","body":"New resident closed a pilot."}'
```

Or open `/suggest` on a phone.

## Slack slash command (no webpage)

Staff can tip from Slack without opening the desk:

```
/suggest-newsletter Keep Bridge visible | Make sure the Bridge launch stays in this issue
```

This hits `POST /slack/suggest`, verifies Slack’s signing secret, then uses the same `ingest_email_recommendation()` path as email-in. Reply is ephemeral: “Got it — … is in Bader’s inbox, no login needed.”

### One-time Slack app setup

1. https://api.slack.com/apps → **Create New App** → **From a manifest** → paste `slack-app-manifest.yaml` (or create manually).
2. Under **Slash Commands**, confirm Request URL is `https://volta-newsletter.fly.dev/slack/suggest`.
3. **Basic Information** → copy **Signing Secret**.
4. Set it on the host (never commit it):

```bash
fly secrets set SLACK_SIGNING_SECRET=your-signing-secret
```

5. **Install App** to the Volta workspace. Matt / Rishabh / Laura / Amy can use the command immediately — no desk login.

Unsigned or forged Slack posts are rejected with HTTP 401. If `SLACK_SIGNING_SECRET` is unset, the endpoint refuses all requests.

### Channel notifications (`#newsletter-desk`)

When `SLACK_WEBHOOK_URL` is set (Incoming Webhook into `#newsletter-desk`):

1. **Draft built** — subject, story count, short includes list, link to `/review`
2. **Send confirmed** — recipient count, plus which pending staff tips did **not** make this issue (so Matt/Laura don’t have to open the app to check)

If the webhook is missing or Slack is down, the build/send still succeeds — failures are logged only.

```bash
fly secrets set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... \
  VOLTA_PUBLIC_URL=https://volta-newsletter.fly.dev
```

### Founder consent DMs (Ask in Slack)

On **Staff recommendations**, tips with consent `not_requested` show **Ask in Slack**. That opens a short form:

1. Enter the approver’s **work email** or **Slack member ID** (U…) — the person Bader would message by hand
2. Desk DMs them: “OK to use this in the newsletter?” with **Approve** / **Decline**
3. Their tap updates `consent_status` on the tip; Bader rebuilds / sends as usual

Contacts are remembered in `VOLTA_DATA_DIR/slack_contacts.json` (no code edit required).

```bash
fly secrets set SLACK_BOT_TOKEN=xoxb-...
```

Bot scopes: `chat:write`, `im:write`, `users:read.email`. Interactivity URL: `https://volta-newsletter.fly.dev/slack/interactive`.

## Internal signals (manual)

Drop JSON files in `data/internal/` (attendance, Bridge, call notes). Each needs `consent_status`. Only **approved** items appear under **From Volta's own activity**. Toggle consent at `/internal`.

## Live Mailchimp later

Host env (not `.env` in git):

```
DEMO_MODE=false
MAILCHIMP_API_KEY=...
MAILCHIMP_SERVER_PREFIX=usX
MAILCHIMP_AUDIENCE_ID=...
```

## License

Internal Volta use.
