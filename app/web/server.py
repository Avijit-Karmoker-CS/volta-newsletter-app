"""Responsive web desk — works on phone and desktop browsers."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.services import ingest as ingest_svc
from app.services import mailchimp_svc
from app.services import newsletter as newsletter_svc
from app.services import research as research_svc
from app.services import storage
from app.services.ingest import IngestError
from app.services.staff import STAFF, authenticate, can_send, desk_logins

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

_DEMO_SESSION_SECRET = "volta-internal-demo-secret"


def _session_secret() -> str:
    """Session signing key — must be set via env on any public/hosted deploy."""
    secret = (os.getenv("VOLTA_SESSION_SECRET") or "").strip()
    if secret and secret != _DEMO_SESSION_SECRET:
        return secret
    # Local laptop only. Never ship the hardcoded demo secret to a public URL.
    if os.getenv("RENDER") or os.getenv("FLY_APP_NAME") or os.getenv("RAILWAY_ENVIRONMENT"):
        raise RuntimeError(
            "VOLTA_SESSION_SECRET must be set to a unique random value on the host "
            "(e.g. openssl rand -hex 32). Do not use the local demo default."
        )
    return _DEMO_SESSION_SECRET


app = FastAPI(title="Volta Newsletter")
app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret(),
    same_site="lax",
    https_only=bool(os.getenv("RENDER") or os.getenv("FLY_APP_NAME") or os.getenv("RAILWAY_ENVIRONMENT")),
)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


def _user(request: Request):
    username = request.session.get("username")
    if not username:
        return None
    return STAFF.get(username)


def _require_user(request: Request):
    user = _user(request)
    if not user:
        return None, RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return user, None


def _ctx(request: Request, **extra):
    user = _user(request)
    mc = mailchimp_svc.status()
    from app.services import settings as settings_svc

    return {
        "request": request,
        "user": user,
        "mailchimp": mc,
        "staff_list": desk_logins(),
        "all_staff": list(STAFF.values()),
        "cadence": settings_svc.newsletter_cadence(),
        "cadence_label": settings_svc.cadence_label(),
        "desk_title": settings_svc.desk_title(),
        **extra,
    }


@app.on_event("startup")
def _startup() -> None:
    storage.seed_recommendations_if_empty()


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if _user(request):
        return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/suggest", response_class=HTMLResponse)
def suggest_page(request: Request):
    """No-login page that simulates emailing a tip into the newsletter desk."""
    flash = request.session.pop("flash", None)
    error = request.session.pop("error", None)
    return templates.TemplateResponse(
        request,
        "suggest.html",
        _ctx(request, flash=flash, error=error),
    )


@app.post("/ingest/email")
async def ingest_email(request: Request):
    """Simulate email-in: create a recommendation without logging into the app.

    Accepts JSON: {"from"|"sender", "subject", "body", optional "token"}
    or form fields (from the /suggest page).
    """
    content_type = (request.headers.get("content-type") or "").lower()
    token = request.headers.get("X-Volta-Ingest-Token")
    via_form = False

    if "application/json" in content_type:
        payload = await request.json()
        sender = str(payload.get("from") or payload.get("sender") or "")
        subject = str(payload.get("subject") or "")
        body = str(payload.get("body") or payload.get("text") or "")
        token = str(payload.get("token") or token or "")
    else:
        form = await request.form()
        sender = str(form.get("sender") or form.get("from") or "")
        subject = str(form.get("subject") or "")
        body = str(form.get("body") or "")
        token = str(form.get("token") or token or "")
        via_form = str(form.get("via") or "") == "form"

    try:
        result = ingest_svc.ingest_email_recommendation(
            subject=subject,
            body=body,
            sender=sender,
            token=token,
        )
    except IngestError as exc:
        if via_form:
            request.session["error"] = str(exc)
            return RedirectResponse("/suggest", status_code=status.HTTP_303_SEE_OTHER)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

    if via_form:
        request.session["flash"] = (
            f"Thanks {result['author']} — “{result['title']}” is in Bader’s inbox "
            "(no app login needed)."
        )
        return RedirectResponse("/suggest", status_code=status.HTTP_303_SEE_OTHER)

    return JSONResponse(result, status_code=201)


@app.post("/slack/suggest")
async def slack_suggest(request: Request):
    """Slash command: /suggest-newsletter Title | Body → same inbox as email-in.

    Verifies Slack signing secret, then calls ingest_email_recommendation().
    Responds within Slack's 3s window with an ephemeral confirmation.
    """
    from app.services import slack as slack_svc
    from app.services.slack import SlackAuthError

    body = await request.body()
    try:
        slack_svc.verify_slack_request(
            body=body,
            timestamp=request.headers.get("X-Slack-Request-Timestamp"),
            signature=request.headers.get("X-Slack-Signature"),
        )
    except SlackAuthError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=401)

    # Re-parse form from the verified raw body (application/x-www-form-urlencoded).
    from urllib.parse import parse_qs

    form = {k: (v[0] if v else "") for k, v in parse_qs(body.decode("utf-8"), keep_blank_values=True).items()}
    text = str(form.get("text") or "").strip()
    # Slack slash payloads expose user_name; map via resolve_sender like email-in.
    sender = str(form.get("user_name") or form.get("user_id") or "Staff")

    if not text:
        return JSONResponse(slack_svc.slack_ephemeral(slack_svc.USAGE))

    try:
        subject, note = slack_svc.parse_suggest_text(text)
    except ValueError:
        return JSONResponse(slack_svc.slack_ephemeral(slack_svc.USAGE))

    try:
        # Signature already proved the caller is Slack — supply the configured
        # EMAIL_IN_TOKEN (if any) so ingest's optional gate still passes.
        result = ingest_svc.ingest_email_recommendation(
            subject=subject,
            body=note,
            sender=sender,
            token=ingest_svc.email_in_token() or None,
        )
    except IngestError as exc:
        return JSONResponse(
            slack_svc.slack_ephemeral(f"Couldn’t save that tip: {exc}"),
            status_code=200,
        )

    return JSONResponse(
        slack_svc.slack_ephemeral(
            f"Got it — “{result['title']}” is in Bader’s inbox, no login needed."
        )
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _user(request):
        return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request,
        "login.html",
        _ctx(request, error=None),
    )


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    pin: str = Form(...),
):
    member = authenticate(username, pin)
    if not member:
        return templates.TemplateResponse(
            request,
            "login.html",
            _ctx(request, error="Wrong PIN — try again."),
            status_code=400,
        )
    request.session["username"] = member.username
    return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    draft = storage.load_latest_draft()
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        request,
        "home.html",
        _ctx(request, draft=draft, flash=flash),
    )


@app.post("/build/default")
def build_default(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    try:
        draft = newsletter_svc.build_default_newsletter()
        request.session["flash"] = f"Draft ready: {draft.get('subject')}"
    except Exception as exc:  # noqa: BLE001
        request.session["flash"] = f"Build failed: {exc}"
    return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/customize", response_class=HTMLResponse)
def customize_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    open_recs = storage.active_recommendations()
    return templates.TemplateResponse(
        request,
        "customize.html",
        _ctx(request, open_recs=open_recs, error=None),
    )


@app.post("/customize")
async def customize_submit(request: Request, plan: str = Form(...)):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    try:
        draft = newsletter_svc.build_custom_newsletter(plan)
        request.session["flash"] = f"Custom draft ready: {draft.get('subject')}"
        return RedirectResponse("/review", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as exc:  # noqa: BLE001
        open_recs = storage.active_recommendations()
        return templates.TemplateResponse(
            request,
            "customize.html",
            _ctx(request, open_recs=open_recs, error=str(exc), plan=plan),
            status_code=400,
        )


@app.get("/recommendations", response_class=HTMLResponse)
def recommendations_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    active = storage.active_recommendations()
    held = storage.held_recommendations()
    included = [r for r in storage.list_recommendations() if r.get("included")]
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        request,
        "recommendations.html",
        _ctx(
            request,
            active_recs=active,
            held_recs=held,
            included_recs=included,
            error=None,
            flash=flash,
        ),
    )


@app.post("/recommendations")
def recommendations_submit(
    request: Request,
    title: str = Form(...),
    body: str = Form(...),
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    if not title.strip() or not body.strip():
        return templates.TemplateResponse(
            request,
            "recommendations.html",
            _ctx(
                request,
                active_recs=storage.active_recommendations(),
                held_recs=storage.held_recommendations(),
                included_recs=[r for r in storage.list_recommendations() if r.get("included")],
                error="Title and body are required.",
            ),
            status_code=400,
        )
    storage.save_recommendation(user.display_name, title, body)
    request.session["flash"] = "Recommendation saved (consent: not requested)."
    return RedirectResponse("/recommendations", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/recommendations/{rec_id}/consent")
def recommendations_consent(
    request: Request,
    rec_id: str,
    consent_status: str = Form(...),
):
    """Bader marks founder consent the way he already does by hand."""
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    updated = storage.set_consent_status(rec_id, consent_status)
    if not updated:
        request.session["flash"] = "Recommendation not found."
    else:
        label = storage.normalize_consent(updated.get("consent_status"))
        request.session["flash"] = f"Consent → {label} for “{updated.get('title')}”."
    return RedirectResponse("/recommendations", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/recommendations/{rec_id}/hold")
def recommendations_hold(
    request: Request,
    rec_id: str,
    held: str = Form("1"),
):
    """Park or release a story ('check back next month')."""
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    want_held = held.strip().lower() in {"1", "true", "yes", "on", "held"}
    updated = storage.set_held(rec_id, want_held)
    if not updated:
        request.session["flash"] = "Recommendation not found."
    elif want_held:
        request.session["flash"] = f"Held for later: “{updated.get('title')}”."
    else:
        request.session["flash"] = f"Back in the active list: “{updated.get('title')}”."
    return RedirectResponse("/recommendations", status_code=status.HTTP_303_SEE_OTHER)


def _ensure_preview_html(draft: dict) -> dict:
    """Rebuild older drafts so preview shows the styled letter (not raw source era)."""
    html = draft.get("html") or ""
    if "0b1c2c" in html and "<img" in html:
        return draft
    if draft.get("mode") == "custom" and draft.get("plan"):
        return newsletter_svc.build_custom_newsletter(draft["plan"])
    return newsletter_svc.build_default_newsletter()


@app.get("/review", response_class=HTMLResponse)
def review_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    draft = storage.load_latest_draft()
    if not draft:
        request.session["flash"] = "No draft yet — build one first."
        return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    draft = _ensure_preview_html(draft)
    # Refresh consent flags from storage (in case Bader toggled after build)
    _sync_draft_consent(draft)
    members = mailchimp_svc.list_community_members()
    flash = request.session.pop("flash", None)
    consent_issues = storage.draft_unapproved_stories(draft)
    return templates.TemplateResponse(
        request,
        "review.html",
        _ctx(
            request,
            draft=draft,
            members=members,
            can_send=can_send(user),
            flash=flash,
            send_result=None,
            consent_issues=consent_issues,
        ),
    )


def _sync_draft_consent(draft: dict) -> None:
    """Attach live consent_status onto draft staff_blocks / internal features."""
    by_id = {r.get("_id"): r for r in storage.list_recommendations()}
    for block in draft.get("staff_blocks") or []:
        rid = block.get("_id")
        if rid and rid in by_id:
            block["consent_status"] = storage.normalize_consent(
                by_id[rid].get("consent_status")
            )
        else:
            block["consent_status"] = storage.normalize_consent(
                block.get("consent_status")
            )

    internal_live = {s.get("_id"): s for s in research_svc.fetch_internal_signals()}
    for item in draft.get("featured_internal") or []:
        rid = item.get("_id")
        if rid and rid in internal_live:
            item["consent_status"] = storage.normalize_consent(
                internal_live[rid].get("consent_status")
            )
        else:
            item["consent_status"] = storage.normalize_consent(
                item.get("consent_status")
            )
    storage.save_draft(draft)


@app.get("/internal", response_class=HTMLResponse)
def internal_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    flash = request.session.pop("flash", None)
    signals = research_svc.fetch_internal_signals(approved_only=False)
    return templates.TemplateResponse(
        request,
        "internal.html",
        _ctx(request, signals=signals, flash=flash),
    )


@app.post("/internal/{signal_id}/consent")
def internal_consent(
    request: Request,
    signal_id: str,
    consent_status: str = Form(...),
):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    updated = research_svc.set_internal_consent(signal_id, consent_status)
    if not updated:
        request.session["flash"] = "Internal signal not found."
    else:
        request.session["flash"] = (
            f"Consent → {storage.normalize_consent(updated.get('consent_status'))} "
            f"for “{updated.get('title')}”."
        )
    return RedirectResponse("/internal", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/preview", response_class=HTMLResponse)
def preview_letter(request: Request):
    """Render the draft exactly as a recipient would see it (for iframe + full tab)."""
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    draft = storage.load_latest_draft()
    if not draft:
        return HTMLResponse(
            "<!DOCTYPE html><html><body style='font-family:sans-serif;padding:24px'>"
            "<p>No draft to preview. Build a newsletter first.</p></body></html>",
            status_code=404,
        )
    draft = _ensure_preview_html(draft)
    return HTMLResponse(content=draft["html"], media_type="text/html")


@app.post("/review/send")
async def review_send(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    if not can_send(user):
        request.session["flash"] = "Only Bader or Matt can send."
        return RedirectResponse("/review", status_code=status.HTTP_303_SEE_OTHER)

    draft = storage.load_latest_draft()
    if not draft:
        request.session["flash"] = "No draft to send."
        return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)

    _sync_draft_consent(draft)
    consent_issues = storage.draft_unapproved_stories(draft)
    if consent_issues:
        titles = ", ".join(
            f"“{i.get('title')}” ({i.get('consent_status')})" for i in consent_issues
        )
        request.session["flash"] = (
            f"Blocked: founder consent not approved for {titles}. "
            "Mark approved on Staff recommendations, rebuild, then send."
        )
        return RedirectResponse("/review", status_code=status.HTTP_303_SEE_OTHER)

    form = await request.form()
    html = str(form.get("html") or draft.get("html") or "")
    selected_ids = set(form.getlist("member_id"))
    members = mailchimp_svc.list_community_members()
    selected = [m for m in members if m.get("id") in selected_ids]
    if not selected:
        request.session["flash"] = "Select at least one community member."
        return RedirectResponse("/review", status_code=status.HTTP_303_SEE_OTHER)

    subject = draft.get("subject", "Volta newsletter")
    draft["html"] = html
    storage.save_draft(draft)
    storage.save_html(html, draft.get("week_of"))

    try:
        result = mailchimp_svc.create_campaign_and_send(
            subject=subject,
            html=html,
            send_now=True,
            recipients=selected,
        )
        draft["status"] = "sent_demo" if result.get("demo") else "sent"
        draft["mailchimp"] = result
        storage.save_draft(draft)
        # Only recs that made it into this draft's staff_blocks (pending[:6])
        storage.mark_draft_staff_recs_included(draft)
        mode = "DEMO" if result.get("demo") else "LIVE"
        request.session["flash"] = (
            f"{mode} send complete · {len(selected)} members · campaign {result.get('campaign_id')}"
        )
    except Exception as exc:  # noqa: BLE001
        request.session["flash"] = f"Send failed: {exc}"

    return RedirectResponse("/review", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    logs = storage.list_send_logs()
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        request,
        "history.html",
        _ctx(request, logs=logs, flash=flash),
    )


@app.post("/history/{send_id}/outcome")
def history_outcome(
    request: Request,
    send_id: str,
    outcome: str = Form(""),
):
    """Manual downstream outcome (attendance / signups) — not Mailchimp opens."""
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    if not can_send(user):
        request.session["flash"] = "Only Bader or Matt can update outcomes."
        return RedirectResponse("/history", status_code=status.HTTP_303_SEE_OTHER)
    updated = storage.update_send_outcome(send_id, outcome)
    if not updated:
        request.session["flash"] = "Send log not found."
    else:
        request.session["flash"] = "Outcome saved."
    return RedirectResponse("/history", status_code=status.HTTP_303_SEE_OTHER)


def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_web(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    ip = local_ip()
    print("")
    print("  Volta Newsletter desk is running")
    print(f"  Desktop:  http://127.0.0.1:{port}")
    print(f"  Phone:    http://{ip}:{port}  (same Wi‑Fi)")
    print("  Login:    Bader / 1111")
    print("  Quit:     Ctrl+C")
    print("")
    uvicorn.run(app, host=host, port=port, log_level="info")
