# Volta Newsletter App

Internal **terminal desk** for Volta’s weekly community newsletter (Bader + staff).  
Runs in your Mac Terminal — **not** a web app, and **not** macOS system Tk (which caused the blank window).

## Why terminal UI?

Apple’s system Python ships a deprecated Tk that often opens a blank CustomTkinter window.  
This app uses [Textual](https://textual.textualize.io/) so it works on your Mac today.

## Quick start

```bash
cd volta-newsletter-app
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # already demo-ready
python main.py
```

Use arrow keys / mouse in the Terminal window. Quit with `Ctrl+C`.

### Demo staff PINs

| Person   | PIN  | Role        |
|----------|------|-------------|
| Bader    | 1111 | editor      |
| Matt     | 2222 | admin       |
| Rishabh  | 3333 | contributor |
| Laura    | 4444 | contributor |
| Amy      | 5555 | contributor |

## Flow

1. Sign in as Bader  
2. **Build from template** or **Customize newsletter**  
3. Staff can add recommendations anytime  
4. **Review & email community** → select members → send  
5. **Send history** shows demo/live campaigns  

Demo Mailchimp is on by default (no real API key). No live email is sent until you add a real key and set `DEMO_MODE=false`.

## Optional later: real Mailchimp GUI

If you install Homebrew Python with Tk (`brew install python@3.12 python-tk@3.12`), the older CustomTkinter screens under `app/ui/` can be revived. Until then, use `python main.py` (Textual).

## License

Internal Volta use.
