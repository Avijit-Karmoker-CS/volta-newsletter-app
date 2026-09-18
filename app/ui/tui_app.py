"""Volta Newsletter — terminal desk (no Tk / no blank macOS window)."""

from __future__ import annotations

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
    OptionList,
    Select,
    Static,
    TextArea,
)
from textual.widgets.option_list import Option

from app.services import mailchimp_svc
from app.services import newsletter as newsletter_svc
from app.services import storage
from app.services.staff import STAFF, StaffMember, authenticate, can_send


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginScreen(Screen):
    CSS = """
    LoginScreen { align: center middle; }
    #login-card {
        width: 64;
        height: auto;
        border: round #c45c26;
        padding: 1 2;
        background: #1c1c1c;
    }
    #login-title { color: #c45c26; text-style: bold; }
    #login-error { color: #e85d4c; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="login-card"):
            yield Static("VOLTA", id="login-title")
            yield Static("Newsletter desk · internal (terminal UI)")
            yield Static("")
            yield Label("Staff member")
            yield Select(
                options=[(m.display_name, m.username) for m in STAFF.values()],
                value="bader",
                id="user-select",
                allow_blank=False,
            )
            yield Label("PIN")
            yield Input(placeholder="PIN (Bader = 1111)", password=True, id="pin-input")
            yield Static("", id="login-error")
            yield Button("Enter desk", variant="primary", id="login-btn")
            yield Static("PINs: Bader 1111 · Matt 2222 · Rishabh 3333 · Laura 4444 · Amy 5555")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self._try_login()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "pin-input":
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


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------


class HomeScreen(Screen):
    BINDINGS = [
        Binding("q", "app.pop_screen", "Back", show=False),
    ]

    CSS = """
    #home { padding: 1 2; }
    .brand { color: #c45c26; text-style: bold; }
    .muted { color: #9a958c; }
    .row { height: auto; margin: 1 0; }
    Button { margin-right: 1; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        user: StaffMember = self.app.user
        draft = storage.load_latest_draft()
        mc = mailchimp_svc.status()
        mode = "DEMO Mailchimp" if mc.get("demo") else "LIVE Mailchimp"

        yield Header(show_clock=True)
        with VerticalScroll(id="home"):
            yield Static("VOLTA", classes="brand")
            yield Static(f"Monday newsletter desk · {user.display_name}")
            yield Static(
                "Default = popular template + staff picks. Customize when you have a plan.",
                classes="muted",
            )
            yield Static(f"{mode} · audience {mc.get('audience_id')}", classes="muted")
            yield Static("")
            with Horizontal(classes="row"):
                yield Button("Build from template", id="btn-default", variant="default")
                yield Button("Customize newsletter", id="btn-custom", variant="primary")
                yield Button("Staff recommendations", id="btn-recs")
            with Horizontal(classes="row"):
                yield Button("Review & email community", id="btn-review", variant="success")
                yield Button("Send history", id="btn-history")
                yield Button("Log out", id="btn-logout")
            yield Static("")
            yield Static("Current draft", classes="brand")
            if draft:
                yield Static(
                    f"Week of {draft.get('week_of')} · {draft.get('mode')} · {draft.get('status')}\n"
                    f"Subject: {draft.get('subject')}"
                )
            else:
                yield Static("No draft yet. Build from template or customize.", classes="muted")
            yield Static("", id="home-status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#home-status", Static)
        if bid == "btn-default":
            status.update("Building popular template…")
            try:
                draft = newsletter_svc.build_default_newsletter()
                status.update(f"Draft ready: {draft.get('subject')}")
                self.app.pop_screen()
                self.app.push_screen(HomeScreen())
            except Exception as exc:  # noqa: BLE001
                status.update(f"Failed: {exc}")
        elif bid == "btn-custom":
            self.app.push_screen(CustomizeScreen())
        elif bid == "btn-recs":
            self.app.push_screen(RecommendationsScreen())
        elif bid == "btn-review":
            draft = storage.load_latest_draft()
            if not draft:
                status.update("Generate a draft first.")
                return
            self.app.push_screen(ReviewScreen(draft))
        elif bid == "btn-history":
            self.app.push_screen(HistoryScreen())
        elif bid == "btn-logout":
            self.app.user = None
            self.app.pop_screen()


# ---------------------------------------------------------------------------
# Customize
# ---------------------------------------------------------------------------


class CustomizeScreen(Screen):
    CSS = """
    #custom { padding: 1 2; }
    #plan { height: 10; }
    #custom-preview { height: 12; }
    """

    def compose(self) -> ComposeResult:
        open_recs = [r for r in storage.list_recommendations() if not r.get("included")]
        yield Header(show_clock=True)
        with VerticalScroll(id="custom"):
            yield Static("Customize newsletter", classes="brand")
            yield Static(
                "Describe this week’s plan. Research + staff recommendations will be folded in.",
                classes="muted",
            )
            yield Static(f"Open staff recommendations: {len(open_recs)}", classes="muted")
            yield TextArea(
                "Lead with this week’s three gatherings. Include any founder wins Laura flagged. "
                "Keep yoga/coffee off unless the calendar is thin.",
                id="plan",
            )
            yield Static("", id="custom-status")
            with Horizontal():
                yield Button("Research & build draft", id="btn-build", variant="primary")
                yield Button("Back", id="btn-back")
            yield TextArea("", id="custom-preview", read_only=True)
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
            return
        if event.button.id == "btn-build":
            plan = self.query_one("#plan", TextArea).text
            status = self.query_one("#custom-status", Static)
            status.update("Researching…")
            try:
                draft = newsletter_svc.build_custom_newsletter(plan)
                notes = (draft.get("research") or {}).get("narrative") or draft.get("subject", "")
                self.query_one("#custom-preview", TextArea).load_text(notes)
                status.update("Draft ready — opening review…")
                self.app.push_screen(ReviewScreen(draft))
            except Exception as exc:  # noqa: BLE001
                status.update(f"Failed: {exc}")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class RecommendationsScreen(Screen):
    CSS = """
    #recs { padding: 1 2; }
    #rec-body { height: 6; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="recs"):
            yield Static("Staff recommendations", classes="brand")
            yield Static(f"Adding as {self.app.user.display_name}", classes="muted")
            yield Input(placeholder="Title", id="rec-title")
            yield TextArea("", id="rec-body")
            with Horizontal():
                yield Button("Save recommendation", id="btn-save", variant="primary")
                yield Button("Back", id="btn-back")
            yield Static("", id="rec-list")
        yield Footer()
        self._refresh_list()

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        lines = []
        for r in storage.list_recommendations():
            badge = "included" if r.get("included") else "open"
            lines.append(f"• [{badge}] {r.get('author')}: {r.get('title')} — {r.get('body')}")
        text = "\n".join(lines) if lines else "No recommendations yet."
        try:
            self.query_one("#rec-list", Static).update(text)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()
            return
        if event.button.id == "btn-save":
            title = self.query_one("#rec-title", Input).value.strip()
            body = self.query_one("#rec-body", TextArea).text.strip()
            if not title or not body:
                return
            storage.save_recommendation(self.app.user.display_name, title, body)
            self.query_one("#rec-title", Input).value = ""
            self.query_one("#rec-body", TextArea).load_text("")
            self._refresh_list()


# ---------------------------------------------------------------------------
# Review + send
# ---------------------------------------------------------------------------


class ReviewScreen(Screen):
    CSS = """
    #review { padding: 1 2; }
    #html-view { height: 14; }
    #members { height: auto; max-height: 16; }
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
                "Demo Mailchimp — full send flow, no live email."
                if mc.get("demo")
                else "Live Mailchimp — will create a real campaign.",
                classes="muted",
            )
            yield Label("Newsletter HTML (editable)")
            yield TextArea(self.draft.get("html", ""), id="html-view")
            yield Static("")
            yield Static("Email to community — uncheck to exclude", classes="brand")
            with Vertical(id="members"):
                for m in self.members:
                    label = f"{m.get('name') or ''} <{m.get('email')}>"
                    yield Checkbox(label, value=True, id=f"m-{m.get('id')}")
            yield Static("", id="send-status")
            with Horizontal():
                if can_send(user):
                    yield Button("Email to community", id="btn-send", variant="success")
                yield Button("Select all", id="btn-all")
                yield Button("Clear", id="btn-clear")
                yield Button("Back", id="btn-back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-back":
            self.app.pop_screen()
            return
        if bid == "btn-all":
            for cb in self.query(Checkbox):
                cb.value = True
            return
        if bid == "btn-clear":
            for cb in self.query(Checkbox):
                cb.value = False
            return
        if bid == "btn-send":
            self._send()

    def _send(self) -> None:
        status = self.query_one("#send-status", Static)
        selected = []
        for m in self.members:
            cb = self.query_one(f"#m-{m.get('id')}", Checkbox)
            if cb.value:
                selected.append(m)
        if not selected:
            status.update("Select at least one community member.")
            return

        html = self.query_one("#html-view", TextArea).text
        subject = self.draft.get("subject", "Volta newsletter")
        self.draft["html"] = html
        storage.save_draft(self.draft)
        storage.save_html(html, self.draft.get("week_of"))

        status.update("Creating campaign…")
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
                f"{mode} send complete · {len(selected)} members · campaign {result.get('campaign_id')}"
            )
        except Exception as exc:  # noqa: BLE001
            status.update(f"Send failed: {exc}")


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


class HistoryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Static("Send history", classes="brand")
            logs = storage.list_send_logs()
            if not logs:
                yield Static("No sends yet.", classes="muted")
            else:
                for item in logs:
                    mode = "DEMO" if item.get("demo") else "LIVE"
                    yield Static(
                        f"{mode} · {item.get('created_at')} · {item.get('campaign_id')}\n"
                        f"  {item.get('subject')} · {item.get('recipient_count', 0)} recipients"
                    )
            yield Button("Back", id="btn-back")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class VoltaNewsletterApp(App):
    TITLE = "Volta Newsletter"
    SUB_TITLE = "Internal desk"
    CSS = """
    Screen { background: #121212; }
    .brand { color: #c45c26; text-style: bold; }
    .muted { color: #9a958c; }
    Header { background: #1c1c1c; }
    Footer { background: #1c1c1c; }
    Button.-primary { background: #c45c26; }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.user: StaffMember | None = None

    def on_mount(self) -> None:
        storage.seed_recommendations_if_empty()
        self.push_screen(LoginScreen())


def run_app() -> None:
    VoltaNewsletterApp().run()
