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

Staff tip without logging in: open **/suggest** or `POST /ingest/email`.

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
