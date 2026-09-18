"""Responsive web desk — works on phone and desktop browsers."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.services import mailchimp_svc
from app.services import newsletter as newsletter_svc
from app.services import storage
from app.services.staff import STAFF, authenticate, can_send

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI(title="Volta Newsletter")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("VOLTA_SESSION_SECRET", "volta-internal-demo-secret"),
    same_site="lax",
    https_only=False,
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
    return {
        "request": request,
        "user": user,
        "mailchimp": mc,
        "staff_list": list(STAFF.values()),
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


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _user(request):
        return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", _ctx(request, error=None))


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    pin: str = Form(...),
):
    member = authenticate(username, pin)
    if not member:
        return templates.TemplateResponse(
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
    open_recs = [r for r in storage.list_recommendations() if not r.get("included")]
    return templates.TemplateResponse(
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
        open_recs = [r for r in storage.list_recommendations() if not r.get("included")]
        return templates.TemplateResponse(
            "customize.html",
            _ctx(request, open_recs=open_recs, error=str(exc), plan=plan),
            status_code=400,
        )


@app.get("/recommendations", response_class=HTMLResponse)
def recommendations_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    recs = storage.list_recommendations()
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        "recommendations.html",
        _ctx(request, recs=recs, error=None, flash=flash),
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
        recs = storage.list_recommendations()
        return templates.TemplateResponse(
            "recommendations.html",
            _ctx(request, recs=recs, error="Title and body are required."),
            status_code=400,
        )
    storage.save_recommendation(user.display_name, title, body)
    request.session["flash"] = "Recommendation saved."
    return RedirectResponse("/recommendations", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/review", response_class=HTMLResponse)
def review_page(request: Request):
    user, redirect = _require_user(request)
    if redirect:
        return redirect
    draft = storage.load_latest_draft()
    if not draft:
        request.session["flash"] = "No draft yet — build one first."
        return RedirectResponse("/home", status_code=status.HTTP_303_SEE_OTHER)
    members = mailchimp_svc.list_community_members()
    flash = request.session.pop("flash", None)
    return templates.TemplateResponse(
        "review.html",
        _ctx(
            request,
            draft=draft,
            members=members,
            can_send=can_send(user),
            flash=flash,
            send_result=None,
        ),
    )


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
        for r in storage.list_recommendations():
            if not r.get("included") and r.get("_id"):
                storage.mark_recommendation_included(r["_id"], True)
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
    return templates.TemplateResponse("history.html", _ctx(request, logs=logs))


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
