"""Review + email to community via Mailchimp (live or full demo)."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from tempfile import NamedTemporaryFile

import customtkinter as ctk

from app.services import mailchimp_svc
from app.services import storage
from app.services.staff import StaffMember, can_send


class ReviewFrame(ctk.CTkFrame):
    def __init__(self, master, user: StaffMember, draft: dict, on_back):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.draft = draft
        self.on_back = on_back
        self.members: list[dict] = []
        self.member_vars: list[tuple[ctk.BooleanVar, dict]] = []

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkButton(top, text="← Back", width=80, command=on_back, fg_color="#2a2a2a").pack(side="left")
        ctk.CTkLabel(top, text="Review & send", font=ctk.CTkFont(size=22, weight="bold")).pack(
            side="left", padx=16
        )

        subject = draft.get("subject", "(no subject)")
        ctk.CTkLabel(self, text=subject, font=ctk.CTkFont(size=16), text_color="#f2efe8").pack(
            anchor="w", padx=28
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=12)
        ctk.CTkButton(actions, text="Open HTML preview", command=self._preview_html).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Refresh community list",
            command=self._load_members,
            fg_color="#2a2a2a",
        ).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        left = ctk.CTkFrame(body, corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(left, text="Newsletter HTML", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        self.html_view = ctk.CTkTextbox(left)
        self.html_view.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.html_view.insert("1.0", draft.get("html", ""))

        right = ctk.CTkFrame(body, corner_radius=12, width=340)
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)
        ctk.CTkLabel(right, text="Email to community", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        ctk.CTkLabel(
            right,
            text="Select who receives this issue, review the letter, then send with one click.",
            wraplength=300,
            justify="left",
            text_color="#9a958c",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=12)

        sel = ctk.CTkFrame(right, fg_color="transparent")
        sel.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(sel, text="Select all", width=100, command=lambda: self._set_all(True), fg_color="#2a2a2a").pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(sel, text="Clear", width=80, command=lambda: self._set_all(False), fg_color="#2a2a2a").pack(
            side="left"
        )

        self.member_list = ctk.CTkScrollableFrame(right, height=260)
        self.member_list.pack(fill="both", expand=True, padx=8, pady=4)

        self.status = ctk.CTkLabel(right, text="", wraplength=300, text_color="#c45c26")
        self.status.pack(anchor="w", padx=12, pady=4)

        send_state = "normal" if can_send(user) else "disabled"
        self.send_btn = ctk.CTkButton(
            right,
            text="Email to community",
            height=44,
            fg_color="#c45c26",
            hover_color="#a84c1e",
            state=send_state,
            command=self._send,
        )
        self.send_btn.pack(fill="x", padx=12, pady=(8, 16))

        if not can_send(user):
            self.status.configure(text="Only Bader (editor) or Matt (admin) can send.")
        else:
            mc = mailchimp_svc.status()
            if mc.get("demo"):
                self.status.configure(
                    text="Demo Mailchimp on — send completes the full flow without a real API key."
                )
            else:
                self.status.configure(text="Live Mailchimp — send will create a real campaign.")

        self._load_members()

    def _preview_html(self) -> None:
        html = self.html_view.get("1.0", "end")
        with NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
            tmp.write(html)
            path = Path(tmp.name)
        webbrowser.open(path.as_uri())

    def _load_members(self) -> None:
        for child in self.member_list.winfo_children():
            child.destroy()
        self.member_vars.clear()

        try:
            self.members = mailchimp_svc.list_community_members()
        except Exception as exc:  # noqa: BLE001
            self.members = mailchimp_svc.demo_preview_members()
            self.status.configure(text=f"Using demo list ({exc})")

        for m in self.members:
            var = ctk.BooleanVar(value=True)
            label = m.get("name") or m.get("email")
            cb = ctk.CTkCheckBox(self.member_list, text=f"{label}  <{m.get('email')}>", variable=var)
            cb.pack(anchor="w", pady=2, padx=4)
            self.member_vars.append((var, m))

    def _set_all(self, value: bool) -> None:
        for var, _ in self.member_vars:
            var.set(value)

    def _send(self) -> None:
        selected = [m for var, m in self.member_vars if var.get()]
        if not selected:
            self.status.configure(text="Select at least one community member.")
            return

        html = self.html_view.get("1.0", "end").strip()
        subject = self.draft.get("subject", "Volta newsletter")
        self.draft["html"] = html
        storage.save_draft(self.draft)
        storage.save_html(html, self.draft.get("week_of"))

        self.send_btn.configure(state="disabled")
        mc = mailchimp_svc.status()
        self.status.configure(
            text="Creating demo Mailchimp campaign…" if mc.get("demo") else "Creating Mailchimp campaign…"
        )

        def work():
            try:
                result = mailchimp_svc.create_campaign_and_send(
                    subject=subject,
                    html=html,
                    send_now=True,
                    recipients=selected,
                )
                self.after(0, lambda: self._sent_ok(result, len(selected)))
            except Exception as exc:  # noqa: BLE001
                self.after(0, lambda: self._sent_fail(str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _sent_ok(self, result: dict, count: int) -> None:
        self.send_btn.configure(state="normal")
        self.draft["status"] = "sent_demo" if result.get("demo") else "sent"
        self.draft["mailchimp"] = result
        storage.save_draft(self.draft)
        for r in storage.list_recommendations():
            if not r.get("included") and r.get("_id"):
                storage.mark_recommendation_included(r["_id"], True)

        cid = result.get("campaign_id")
        if result.get("demo"):
            self.status.configure(
                text=(
                    f"Demo send complete · {count} community members · campaign {cid}. "
                    "No live email sent. Replace DEMO keys when you have a real Mailchimp API key."
                )
            )
        else:
            self.status.configure(
                text=f"Sent via Mailchimp ({count} selected). Campaign {cid}."
            )

    def _sent_fail(self, error: str) -> None:
        self.send_btn.configure(state="normal")
        self.status.configure(text=f"Send failed: {error}")
