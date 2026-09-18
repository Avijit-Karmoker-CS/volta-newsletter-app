"""Login screen — internal staff only."""

from __future__ import annotations

import customtkinter as ctk

from app.services.staff import STAFF, StaffMember, authenticate


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master, fg_color="transparent")
        self.on_success = on_success

        card = ctk.CTkFrame(self, corner_radius=16, fg_color="#1c1c1c")
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text="VOLTA",
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold"),
            text_color="#f2efe8",
        ).pack(padx=48, pady=(40, 4))

        ctk.CTkLabel(
            card,
            text="Newsletter desk · internal",
            font=ctk.CTkFont(size=14),
            text_color="#9a958c",
        ).pack(padx=48, pady=(0, 24))

        self.user = ctk.CTkComboBox(
            card,
            values=[m.display_name for m in STAFF.values()],
            width=260,
            height=36,
        )
        self.user.set("Bader")
        self.user.pack(padx=48, pady=6)

        self.pin = ctk.CTkEntry(card, placeholder_text="PIN", show="•", width=260, height=36)
        self.pin.pack(padx=48, pady=6)
        self.pin.bind("<Return>", lambda _e: self._submit())

        self.error = ctk.CTkLabel(card, text="", text_color="#e85d4c", font=ctk.CTkFont(size=12))
        self.error.pack(padx=48, pady=(4, 0))

        ctk.CTkButton(
            card,
            text="Enter desk",
            width=260,
            height=40,
            fg_color="#c45c26",
            hover_color="#a84c1e",
            command=self._submit,
        ).pack(padx=48, pady=(16, 40))

        hint = "Staff: Bader 1111 · Matt 2222 · Rishabh 3333 · Laura 4444 · Amy 5555"
        ctk.CTkLabel(card, text=hint, font=ctk.CTkFont(size=11), text_color="#6e6a63").pack(
            padx=24, pady=(0, 24)
        )

    def _submit(self) -> None:
        name = self.user.get().strip()
        username = next((u for u, m in STAFF.items() if m.display_name == name), name.lower())
        member = authenticate(username, self.pin.get())
        if not member:
            self.error.configure(text="Wrong PIN — try again.")
            return
        self.on_success(member)
