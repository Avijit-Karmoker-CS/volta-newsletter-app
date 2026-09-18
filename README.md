# Volta Newsletter App

Internal **desktop** app for Volta’s weekly community newsletter. Built for Bader (Monday morning or anytime), with access for Matt, Rishabh, Laura, Amy, and other staff.

This is **not** a web frontend. It is a native Python desktop app (CustomTkinter) that works **alongside Mailchimp**.

## Demo mode (no real Mailchimp key needed)

The app ships with a pretend Mailchimp key so you can finish the whole workflow today:

1. Sign in as Bader  
2. Build default **or** customize  
3. Review the HTML  
4. Select community members  
5. Click **Email to community** → demo campaign is created and logged  

No live email is sent in demo mode. When you get a real API key, put it in `.env` and set `DEMO_MODE=false`.

## Quick start

```bash
cd volta-newsletter-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Demo staff PINs

| Person   | Username | PIN  | Role        |
|----------|----------|------|-------------|
| Bader    | bader    | 1111 | editor      |
| Matt     | matt     | 2222 | admin       |
| Rishabh  | rishabh  | 3333 | contributor |
| Laura    | laura    | 4444 | contributor |
| Amy      | amy      | 5555 | contributor |

## What it does

1. **Default generate** — popular template + staff picks + community signals  
2. **Customize** — Bader’s plan → research + staff recommendations → draft  
3. **Staff recommendations** — Matt / Rishabh / Laura / Amy can drop what should go in  
4. **Review** — HTML preview before anything goes out  
5. **Email to community** — select recipients → send via Mailchimp (demo or live)  
6. **Send history** — log of demo/live campaigns from this desk  

## Mailchimp later (live)

```
DEMO_MODE=false
MAILCHIMP_API_KEY=...
MAILCHIMP_SERVER_PREFIX=usX
MAILCHIMP_AUDIENCE_ID=...
```

## Optional AI research

```
OPENAI_API_KEY=...
```

If unset, customize still works with local heuristics + Eventbrite reachability checks.

## Project layout

```
main.py                 # launch desktop app
app/ui/                 # desktop screens
app/services/           # newsletter, research, Mailchimp, storage
data/seed/              # starter staff recommendations
data/local/             # drafts, sends, recommendations (gitignored)
```

## License

Internal Volta use.
