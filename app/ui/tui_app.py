"""Volta Newsletter — terminal desk (works on small 80x24 terminals)."""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TextArea,
)

from app.services import mailchimp_svc
from app.services import newsletter as newsletter_svc
from app.services import storage
from app.services.staff import STAFF, StaffMember, authenticate, can_send


class LoginScreen(Screen):
    BINDINGS = [Binding("enter", "login", "Enter desk", show=True)]

    CSS = """
    LoginScreen { align: center middle; }
    #login-card {
        width: 70;
        height: auto;
        border: round #c45c26;
        padding: 1 2;
        background: #1c1c1c;
    }
    #login-title { color: #c45c26; text-style: bold; }
    #login-error { color: #e85d4c; height: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="login-card"):
            yield Static("VOLTA", id="login-title")
            yield Static("Newsletter desk · internal")
            yield Label("Staff")
            yield Select(
                options=[(m.display_name, m.username) for m in STAFF.values()],
                value="bader",
                id="user-select",
                allow_blank=False,
            )
            yield Label("PIN")
            yield Input(placeholder="Bader = 1111", password=True, id="pin-input")
            yield Static("", id="login-error")
            yield Button("Enter desk", variant="primary", id="login-btn")
            yield Static("PINs: Bader 1111 · Matt 2222 · Rishabh 3333 · Laura 4444 · Amy 5555")
        yield Footer()

    def action_login(self) -> None:
        self._try_login()

    @on(Button.Pressed, "#login-btn")
    def _login_click(self) -> None:
        self._try_login()

    @on(Input.Submitted, "#pin-input")
    def _pin_enter(self) -> None:
        self._try_login()

    def _try_login(self) -> None:
        username = self.query_one("#user-select", Select).value
        pin = self.query_one("#pin-input", Input).value
        member = authenticate(str(username), pin)
        err = self.query_one("#login-error", Static)
        if not member:
            err.update("Wrong PIN — try again.")
            return
        self.app.user = member
        self.app.push_screen(HomeScreen())


class HomeScreen(Screen):
    BINDINGS = [
        Binding("r", "review", "Review & send", show=True),
        Binding("b", "build", "Build", show=True),
        Binding("c", "customize", "Customize", show=True),
        Binding("h", "history", "History", show=True),
        Binding("l", "logout", "Log out", show=True),
    ]

    CSS = """
    #home { padding: 0 1; }
    #actions { dock: bottom; height: 5; padding: 0 1; background: #1c1c1c; }
    .brand { color: #c45c26; text-style: bold; }
    .muted { color: #9a958c; }
    #home-status { color: #c45c26; height: 2; }
    Button { margin-right: 1; }
    """

    def compose(self) -> ComposeResult:
        user: StaffMember = self.app.user
        draft = storage.load_latest_draft()
        mc = mailchimp_svc.status()
        mode = "DEMO" if mc.get("demo") else "LIVE"

        yield Header(show_clock=True)
        with VerticalScroll(id="home"):
            yield Static("VOLTA", classes="brand")
            yield Static(f"Desk · {user.display_name} · Mailchimp {mode}")
            yield Static("Press R to review & send · B to build · C to customize", classes="muted")
            yield Static("")
            yield Static("Current draft", classes="brand")
            if draft:
                yield Static(
                    f"{draft.get('week_of')} · {draft.get('mode')} · {draft.get('status')}\n"
                    f"{draft.get('subject')}"
                )
            else:
                yield Static("No draft yet — press B to build.", classes="muted")
            yield Static("", id="home-status")
        with Vertical(id="actions"):
            with Horizontal():
                yield Button("Build", id="btn-default")
                yield Button("Customize", id="btn-custom", variant="primary")
                yield Button("Recs", id="btn-recs")
            with Horizontal():
                yield Button("Review & send", id="btn-review", variant="success")
                yield Button("History", id="btn-history")
                yield Button("Log out", id="btn-logout")
        yield Footer()

    def _status(self, msg: str) -> None:
        self.query_one("#home-status", Static).update(msg)

    def action_build(self) -> None:
        self._build()

    def action_customize(self) -> None:
        self.app.push_screen(CustomizeScreen())

    def action_review(self) -> None:
        self._open_review()

    def action_history(self) -> None:
        self.app.push_screen(HistoryScreen())

    def action_logout(self) -> None:
        self.app.user = None
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-default")
    def _btn_default(self, event: Button.Pressed) -> None:
        event.stop()
        self._build()

    @on(Button.Pressed, "#btn-custom")
    def _btn_custom(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(CustomizeScreen())

    @on(Button.Pressed, "#btn-recs")
    def _btn_recs(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(RecommendationsScreen())

    @on(Button.Pressed, "#btn-review")
    def _btn_review(self, event: Button.Pressed) -> None:
        event.stop()
        self._open_review()

    @on(Button.Pressed, "#btn-history")
    def _btn_history(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(HistoryScreen())

    @on(Button.Pressed, "#btn-logout")
    def _btn_logout(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_logout()

    def _build(self) -> None:
        self._status("Building…")
        try:
            draft = newsletter_svc.build_default_newsletter()
            self._status(f"Ready: {draft.get('subject')} — press R to review & send")
            # Refresh home so draft summary updates
            self.app.pop_screen()
            self.app.push_screen(HomeScreen())
        except Exception as exc:  # noqa: BLE001
            self._status(f"Failed: {exc}")

    def _open_review(self) -> None:
        draft = storage.load_latest_draft()
        if not draft:
            self._status("No draft — building one now…")
            try:
                draft = newsletter_svc.build_default_newsletter()
            except Exception as exc:  # noqa: BLE001
                self._status(f"Failed: {exc}")
                return
        self.app.push_screen(ReviewScreen(draft))


class CustomizeScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("ctrl+s", "build", "Build", show=True),
    ]

    CSS = """
    #custom { padding: 0 1; }
    #plan { height: 8; }
    #actions { dock: bottom; height: 3; padding: 0 1; background: #1c1c1c; }
    .brand { color: #c45c26; text-style: bold; }
    .muted { color: #9a958c; }
    """

    def compose(self) -> ComposeResult:
        open_recs = [r for r in storage.list_recommendations() if not r.get("included")]
        yield Header(show_clock=True)
        with VerticalScroll(id="custom"):
            yield Static("Customize", classes="brand")
            yield Static(f"Open staff recs: {len(open_recs)}", classes="muted")
            yield TextArea(
                "Lead with this week’s three gatherings. Include Laura wins if public.",
                id="plan",
            )
            yield Static("", id="custom-status")
        with Horizontal(id="actions"):
            yield Button("Research & build", id="btn-build", variant="primary")
            yield Button("Back", id="btn-back")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_build(self) -> None:
        self._build()

    @on(Button.Pressed, "#btn-back")
    def _back(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-build")
    def _build_click(self, event: Button.Pressed) -> None:
        event.stop()
        self._build()

    def _build(self) -> None:
        plan = self.query_one("#plan", TextArea).text
        status = self.query_one("#custom-status", Static)
        status.update("Researching…")
        try:
            draft = newsletter_svc.build_custom_newsletter(plan)
            status.update("Draft ready — opening review…")
            self.app.push_screen(ReviewScreen(draft))
        except Exception as exc:  # noqa: BLE001
            status.update(f"Failed: {exc}")


class RecommendationsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    CSS = """
    #recs { padding: 0 1; }
    #rec-body { height: 5; }
    #actions { dock: bottom; height: 3; padding: 0 1; background: #1c1c1c; }
    .brand { color: #c45c26; text-style: bold; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="recs"):
            yield Static(f"Recommendations · {self.app.user.display_name}", classes="brand")
            yield Input(placeholder="Title", id="rec-title")
            yield TextArea("", id="rec-body")
            yield Static("", id="rec-list")
        with Horizontal(id="actions"):
            yield Button("Save", id="btn-save", variant="primary")
            yield Button("Back", id="btn-back")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        lines = []
        for r in storage.list_recommendations()[:8]:
            badge = "in" if r.get("included") else "open"
            lines.append(f"[{badge}] {r.get('author')}: {r.get('title')}")
        self.query_one("#rec-list", Static).update("\n".join(lines) or "None yet.")

    def action_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def _back(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-save")
    def _save(self, event: Button.Pressed) -> None:
        event.stop()
        title = self.query_one("#rec-title", Input).value.strip()
        body = self.query_one("#rec-body", TextArea).text.strip()
        if not title or not body:
            return
        storage.save_recommendation(self.app.user.display_name, title, body)
        self.query_one("#rec-title", Input).value = ""
        self.query_one("#rec-body", TextArea).load_text("")
        self._refresh_list()


class ReviewScreen(Screen):
    """Actions docked at bottom so they stay visible on 80x24."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("s", "send", "Send now", show=True),
        Binding("a", "select_all", "All", show=False),
        Binding("n", "select_none", "None", show=False),
    ]

    CSS = """
    #review { padding: 0 1; }
    #html-view { height: 6; }
    #actions { dock: bottom; height: 5; padding: 0 1; background: #1c1c1c; }
    #send-status { color: #c45c26; height: 2; }
    .brand { color: #c45c26; text-style: bold; }
    .muted { color: #9a958c; }
    Button { margin-right: 1; }
    """

    def __init__(self, draft: dict):
        super().__init__()
        self.draft = draft
        self.members = mailchimp_svc.list_community_members()

    def compose(self) -> ComposeResult:
        user: StaffMember = self.app.user
        mc = mailchimp_svc.status()
        yield Header(show_clock=True)
        with VerticalScroll(id="review"):
            yield Static("Review & send", classes="brand")
            yield Static(self.draft.get("subject", "(no subject)"))
            yield Static(
                "DEMO — no live email. Press S to send · Esc to go back"
                if mc.get("demo")
                else "LIVE Mailchimp. Press S to send · Esc to go back",
                classes="muted",
            )
            yield Label("HTML")
            yield TextArea(self.draft.get("html", ""), id="html-view")
            yield Static("Community (space to toggle)", classes="brand")
            for m in self.members:
                label = f"{m.get('name') or ''} <{m.get('email')}>"
                yield Checkbox(label, value=True, id=f"m-{m.get('id')}")
        with Vertical(id="actions"):
            yield Static("Ready — press S or click Send now", id="send-status")
            with Horizontal():
                if can_send(user):
                    yield Button("Send now", id="btn-send", variant="success")
                yield Button("All", id="btn-all")
                yield Button("Clear", id="btn-clear")
                yield Button("Back", id="btn-back")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_send(self) -> None:
        if can_send(self.app.user):
            self._send()

    def action_select_all(self) -> None:
        for cb in self.query(Checkbox):
            cb.value = True

    def action_select_none(self) -> None:
        for cb in self.query(Checkbox):
            cb.value = False

    @on(Button.Pressed, "#btn-back")
    def _back(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-all")
    def _all(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_select_all()

    @on(Button.Pressed, "#btn-clear")
    def _clear(self, event: Button.Pressed) -> None:
        event.stop()
        self.action_select_none()

    @on(Button.Pressed, "#btn-send")
    def _send_click(self, event: Button.Pressed) -> None:
        event.stop()
        self._send()

    def _send(self) -> None:
        status = self.query_one("#send-status", Static)
        selected = []
        for m in self.members:
            cb = self.query_one(f"#m-{m.get('id')}", Checkbox)
            if cb.value:
                selected.append(m)
        if not selected:
            status.update("Select at least one member.")
            return

        html = self.query_one("#html-view", TextArea).text
        subject = self.draft.get("subject", "Volta newsletter")
        self.draft["html"] = html
        storage.save_draft(self.draft)
        storage.save_html(html, self.draft.get("week_of"))
        status.update("Sending…")
        try:
            result = mailchimp_svc.create_campaign_and_send(
                subject=subject,
                html=html,
                send_now=True,
                recipients=selected,
            )
            self.draft["status"] = "sent_demo" if result.get("demo") else "sent"
            self.draft["mailchimp"] = result
            storage.save_draft(self.draft)
            for r in storage.list_recommendations():
                if not r.get("included") and r.get("_id"):
                    storage.mark_recommendation_included(r["_id"], True)
            mode = "DEMO" if result.get("demo") else "LIVE"
            status.update(
                f"{mode} sent · {len(selected)} members · {result.get('campaign_id')} · Esc=Back"
            )
        except Exception as exc:  # noqa: BLE001
            status.update(f"Send failed: {exc}")


class HistoryScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    CSS = """
    #actions { dock: bottom; height: 3; padding: 0 1; background: #1c1c1c; }
    .brand { color: #c45c26; text-style: bold; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Send history", classes="brand")
            logs = storage.list_send_logs()
            if not logs:
                yield Static("No sends yet.")
            else:
                for item in logs[:12]:
                    mode = "DEMO" if item.get("demo") else "LIVE"
                    yield Static(
                        f"{mode} · {item.get('created_at')} · {item.get('campaign_id')}\n"
                        f"  {item.get('subject')} · {item.get('recipient_count', 0)} to"
                    )
        with Horizontal(id="actions"):
            yield Button("Back", id="btn-back")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def _back(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.pop_screen()


class VoltaNewsletterApp(App):
    TITLE = "Volta Newsletter"
    SUB_TITLE = "Internal desk"
    CSS = """
    Screen { background: #121212; }
    .brand { color: #c45c26; text-style: bold; }
    .muted { color: #9a958c; }
    Header { background: #1c1c1c; }
    Footer { background: #1c1c1c; }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.user: StaffMember | None = None

    def on_mount(self) -> None:
        storage.seed_recommendations_if_empty()
        self.push_screen(LoginScreen())


def run_app() -> None:
    VoltaNewsletterApp().run()
