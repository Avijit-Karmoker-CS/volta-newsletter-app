"""Send history — demo and live Mailchimp campaign log."""

from __future__ import annotations

import customtkinter as ctk

from app.services import storage
from app.services.staff import StaffMember


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, user: StaffMember, on_back):
        super().__init__(master, fg_color="transparent")
        self.user = user

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkButton(top, text="← Back", width=80, command=on_back, fg_color="#2a2a2a").pack(side="left")
        ctk.CTkLabel(top, text="Send history", font=ctk.CTkFont(size=22, weight="bold")).pack(
            side="left", padx=16
        )

        ctk.CTkLabel(
            self,
            text="Campaigns created from this desk (demo sends included).",
            text_color="#9a958c",
        ).pack(anchor="w", padx=28, pady=(0, 12))

        box = ctk.CTkScrollableFrame(self, corner_radius=12)
        box.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        logs = storage.list_send_logs()
        if not logs:
            ctk.CTkLabel(box, text="No sends yet. Review a draft and email the community.", text_color="#888").pack(
                pady=24
            )
            return

        for item in logs:
            row = ctk.CTkFrame(box, fg_color="#222")
            row.pack(fill="x", pady=6, padx=4)
            mode = "DEMO" if item.get("demo") else "LIVE"
            ctk.CTkLabel(
                row,
                text=f"{mode} · {item.get('created_at', '')} · {item.get('campaign_id', '')}",
                font=ctk.CTkFont(size=12),
                text_color="#9a958c",
            ).pack(anchor="w", padx=12, pady=(10, 0))
            ctk.CTkLabel(
                row,
                text=item.get("subject") or "(no subject)",
                font=ctk.CTkFont(size=16, weight="bold"),
            ).pack(anchor="w", padx=12)
            ctk.CTkLabel(
                row,
                text=f"{item.get('recipient_count', 0)} recipients · status {item.get('status')}",
                text_color="#d6d0c6",
            ).pack(anchor="w", padx=12, pady=(0, 12))
