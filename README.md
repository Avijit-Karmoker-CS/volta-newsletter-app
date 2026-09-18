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

## Optional terminal UI

```bash
python main.py --tui
```

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
