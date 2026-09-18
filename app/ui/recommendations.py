"""Staff recommendation inbox — Matt, Rishabh, Laura, Amy, Bader."""

from __future__ import annotations

import customtkinter as ctk

from app.services import storage
from app.services.staff import StaffMember


class RecommendationsFrame(ctk.CTkFrame):
    def __init__(self, master, user: StaffMember, on_back):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.on_back = on_back

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkButton(top, text="← Back", width=80, command=on_back, fg_color="#2a2a2a").pack(side="left")
        ctk.CTkLabel(
            top,
            text="Staff recommendations",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=16)

        form = ctk.CTkFrame(self, corner_radius=12)
        form.pack(fill="x", padx=28, pady=12)

        ctk.CTkLabel(form, text=f"Add as {user.display_name}", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=16, pady=(16, 8)
        )
        self.title_entry = ctk.CTkEntry(form, placeholder_text="Title (what should go in)", height=36)
        self.title_entry.pack(fill="x", padx=16, pady=4)
        self.body = ctk.CTkTextbox(form, height=100)
        self.body.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(form, text="Save recommendation", command=self._save, fg_color="#c45c26").pack(
            anchor="e", padx=16, pady=(8, 16)
        )

        self.list_box = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.list_box.pack(fill="both", expand=True, padx=28, pady=(8, 24))
        self._refresh()

    def _save(self) -> None:
        title = self.title_entry.get().strip()
        body = self.body.get("1.0", "end").strip()
        if not title or not body:
            return
        storage.save_recommendation(self.user.display_name, title, body)
        self.title_entry.delete(0, "end")
        self.body.delete("1.0", "end")
        self._refresh()

    def _refresh(self) -> None:
        for child in self.list_box.winfo_children():
            child.destroy()
        recs = storage.list_recommendations()
        if not recs:
            ctk.CTkLabel(self.list_box, text="No recommendations yet.", text_color="#888").pack(pady=20)
            return
        for r in recs:
            row = ctk.CTkFrame(self.list_box, fg_color="#222")
            row.pack(fill="x", pady=6, padx=4)
            badge = "included" if r.get("included") else "open"
            ctk.CTkLabel(
                row,
                text=f"{r.get('author')} · {badge}",
                font=ctk.CTkFont(size=12),
                text_color="#9a958c",
            ).pack(anchor="w", padx=12, pady=(10, 0))
            ctk.CTkLabel(row, text=r.get("title", ""), font=ctk.CTkFont(size=16, weight="bold")).pack(
                anchor="w", padx=12
            )
            ctk.CTkLabel(row, text=r.get("body", ""), wraplength=720, justify="left").pack(
                anchor="w", padx=12, pady=(0, 12)
            )
