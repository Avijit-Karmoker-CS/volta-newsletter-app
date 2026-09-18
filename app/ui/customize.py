"""Customize flow — Bader's prompt → research + staff picks → draft."""

from __future__ import annotations

import threading

import customtkinter as ctk

from app.services import newsletter as newsletter_svc
from app.services import storage
from app.services.staff import StaffMember


class CustomizeFrame(ctk.CTkFrame):
    def __init__(self, master, user: StaffMember, on_back, on_draft_ready):
        super().__init__(master, fg_color="#121212")
        self.user = user
        self.on_back = on_back
        self.on_draft_ready = on_draft_ready

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkButton(top, text="← Back", width=80, command=on_back, fg_color="#2a2a2a").pack(side="left")
        ctk.CTkLabel(
            top,
            text="Customize newsletter",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            self,
            text=(
                "Tell the desk what this week should cover. AI researches community / builder "
                "interest signals and folds in open staff recommendations (Matt, Rishabh, Laura, Amy…)."
            ),
            wraplength=780,
            justify="left",
            text_color="#b0aaa0",
        ).pack(anchor="w", padx=28, pady=(4, 12))

        self.plan = ctk.CTkTextbox(self, height=160)
        self.plan.pack(fill="x", padx=28, pady=8)
        self.plan.insert(
            "1.0",
            "Lead with this week’s three gatherings. Include any founder wins Laura flagged. "
            "Keep yoga/coffee off unless the calendar is thin.",
        )

        recs = storage.list_recommendations()
        open_recs = [r for r in recs if not r.get("included")]
        ctk.CTkLabel(
            self,
            text=f"Open staff recommendations: {len(open_recs)}",
            font=ctk.CTkFont(size=13),
            text_color="#9a958c",
        ).pack(anchor="w", padx=28, pady=(8, 4))

        self.status = ctk.CTkLabel(self, text="", text_color="#c45c26")
        self.status.pack(anchor="w", padx=28)

        self.run_btn = ctk.CTkButton(
            self,
            text="Research & build draft",
            height=44,
            fg_color="#c45c26",
            hover_color="#a84c1e",
            command=self._run,
        )
        self.run_btn.pack(anchor="e", padx=28, pady=16)

        self.preview = ctk.CTkTextbox(self, height=280)
        self.preview.pack(fill="both", expand=True, padx=28, pady=(0, 24))

    def _run(self) -> None:
        plan = self.plan.get("1.0", "end").strip()
        self.run_btn.configure(state="disabled")
        self.status.configure(text="Researching community signals and staff picks…")

        def work():
            try:
                draft = newsletter_svc.build_custom_newsletter(plan)
                self.after(0, lambda: self._done(draft, None))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: self._done(None, str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, draft, error: str | None) -> None:
        self.run_btn.configure(state="normal")
        if error:
            self.status.configure(text=f"Failed: {error}")
            return
        self.status.configure(text="Draft ready — opening review…")
        notes = (draft.get("research") or {}).get("narrative") or draft.get("subject", "")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", notes)
        self.after(400, lambda: self.on_draft_ready(draft))
