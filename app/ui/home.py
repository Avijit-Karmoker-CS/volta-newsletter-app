"""Home desk — default generate, customize, recommendations, review."""

from __future__ import annotations

import threading

import customtkinter as ctk

from app.services import mailchimp_svc
from app.services import newsletter as newsletter_svc
from app.services import settings as settings_svc
from app.services import storage
from app.services.staff import StaffMember, can_send


class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, user: StaffMember, navigate):
        super().__init__(master, fg_color="#121212")
        self.user = user
        self.navigate = navigate
        self.current_draft = storage.load_latest_draft()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 8))

        ctk.CTkLabel(
            header,
            text="VOLTA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#c45c26",
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=f"{settings_svc.desk_title()} · {user.display_name}",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(
            header,
            text="This desk decides what goes in and gates consent. Mailchimp still sends.",
            text_color="#9a958c",
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=32, pady=24)

        self._card(
            grid,
            "Generate default",
            "Open staff picks plus consent-approved public and internal signals in the default letter shape.",
            "Build from template",
            self._generate_default,
            0,
        )
        self._card(
            grid,
            "Customize",
            "Your prompt plus research, staff recs, and only consent-approved Volta signals — then you decide what makes the cut.",
            "Customize newsletter",
            lambda: self.navigate("customize"),
            1,
            accent=True,
        )
        self._card(
            grid,
            "Staff recommendations",
            "Everyone on staff can drop what should go in this issue.",
            "Open inbox",
            lambda: self.navigate("recommendations"),
            2,
        )

        status_row = ctk.CTkFrame(self, corner_radius=12)
        status_row.pack(fill="x", padx=32, pady=(8, 12))

        mc = mailchimp_svc.status()
        if mc.get("demo"):
            mc_text = (
                "Mailchimp · DEMO mode (pretend API) · audience "
                f"{mc.get('audience_id')} · full send flow works without a real key"
            )
        else:
            mc_text = f"Mailchimp · LIVE · audience {mc.get('audience_id')}"
        ctk.CTkLabel(status_row, text=mc_text, text_color="#b0aaa0").pack(anchor="w", padx=16, pady=14)

        draft_box = ctk.CTkFrame(self, corner_radius=12)
        draft_box.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        ctk.CTkLabel(draft_box, text="Current draft", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 4)
        )
        self.draft_label = ctk.CTkLabel(
            draft_box,
            text=self._draft_summary(),
            wraplength=760,
            justify="left",
            text_color="#d6d0c6",
        )
        self.draft_label.pack(anchor="w", padx=16, pady=(0, 12))

        btns = ctk.CTkFrame(draft_box, fg_color="transparent")
        btns.pack(anchor="w", padx=16, pady=(0, 16))
        ctk.CTkButton(
            btns,
            text="Review newsletter",
            command=self._review,
            state="normal" if self.current_draft else "disabled",
            width=160,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns,
            text="Email to community…",
            command=self._review,
            fg_color="#c45c26",
            hover_color="#a84c1e",
            state="normal" if self.current_draft and can_send(user) else "disabled",
            width=180,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns,
            text="Send history",
            command=lambda: self.navigate("history"),
            fg_color="#2f2f2f",
            width=120,
        ).pack(side="left")

        self.busy = ctk.CTkLabel(self, text="", text_color="#c45c26")
        self.busy.pack(anchor="w", padx=32, pady=(0, 16))

    def _card(self, parent, title, blurb, button, command, col, accent=False):
        card = ctk.CTkFrame(parent, corner_radius=14, width=240, height=200)
        card.grid(row=0, column=col, padx=8, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=17, weight="bold")).pack(
            anchor="w", padx=16, pady=(18, 6)
        )
        ctk.CTkLabel(card, text=blurb, wraplength=220, justify="left", text_color="#9a958c").pack(
            anchor="w", padx=16
        )
        ctk.CTkButton(
            card,
            text=button,
            command=command,
            fg_color="#c45c26" if accent else "#2f2f2f",
            hover_color="#a84c1e" if accent else "#3a3a3a",
        ).pack(anchor="w", padx=16, pady=(18, 18))

    def _draft_summary(self) -> str:
        d = self.current_draft
        if not d:
            return "No draft yet. Generate the default template or customize."
        return (
            f"Week of {d.get('week_of')} · mode {d.get('mode')} · status {d.get('status')}\n"
            f"Subject: {d.get('subject')}"
        )

    def _generate_default(self) -> None:
        self.busy.configure(text="Building popular template…")

        def work():
            try:
                draft = newsletter_svc.build_default_newsletter()
                self.after(0, lambda: self._default_done(draft, None))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: self._default_done(None, str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _default_done(self, draft, error):
        if error:
            self.busy.configure(text=f"Failed: {error}")
            return
        self.current_draft = draft
        self.draft_label.configure(text=self._draft_summary())
        self.busy.configure(text="Default draft ready — review before emailing the community.")
        self.navigate("home", refresh=True)

    def _review(self) -> None:
        draft = self.current_draft or storage.load_latest_draft()
        if not draft:
            self.busy.configure(text="Generate a draft first.")
            return
        self.navigate("review", draft=draft)
