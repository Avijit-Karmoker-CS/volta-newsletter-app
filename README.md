# Volta Newsletter App

Internal newsletter desk for **Bader and staff** — works on **phone and desktop** in a browser.

Same Wi‑Fi → open the printed Phone URL on your phone. Desktop → open localhost.

## Quick start (phone + desktop)

```bash
cd volta-newsletter-app
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # demo Mailchimp already set
python main.py
```

Then open:

- **Desktop:** http://127.0.0.1:8000  
- **Phone:** http://YOUR-MAC-IP:8000 (printed in the terminal when the app starts — same Wi‑Fi)

Login: **Bader / 1111**

### Demo flow

1. **Build now** or **Customize**  
2. **Review & send**  
3. Keep community members checked  
4. Tap **Email to community** (demo send — no live email)  
5. **Send history** to confirm  

Staff (Laura `4444`, Matt `2222`, etc.) can add recommendations from their phones too.

Staff (Laura, etc.) tip without logging in: open **/suggest** or
`POST /ingest/email` with `{"from","subject","body"}`.

## Optional terminal UI

```bash
python main.py --tui
```

## Email-in (no login)

```bash
curl -s -X POST http://127.0.0.1:8000/ingest/email \
  -H 'Content-Type: application/json' \
  -d '{"from":"laura@voltaeffect.com","subject":"Member win","body":"New resident closed a pilot."}'
```

Or open http://127.0.0.1:8000/suggest on a phone. Same as the in-app recommendations form — Bader sees it in the desk inbox.

Optional: set `EMAIL_IN_TOKEN` in `.env` and send header `X-Volta-Ingest-Token`.

## Live Mailchimp later

In `.env`:

```
DEMO_MODE=false
MAILCHIMP_API_KEY=...
MAILCHIMP_SERVER_PREFIX=usX
MAILCHIMP_AUDIENCE_ID=...
```

## License

Internal Volta use.
