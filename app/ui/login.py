"""Login screen — internal staff only."""

from __future__ import annotations

import customtkinter as ctk

from app.services.staff import STAFF, authenticate


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master, fg_color="#121212")
        self.on_success = on_success

        # Center with pack (place() often renders blank under CustomTkinter on macOS)
        outer = ctk.CTkFrame(self, fg_color="#121212")
        outer.pack(expand=True, fill="both")

        card = ctk.CTkFrame(outer, corner_radius=16, fg_color="#1c1c1c", width=420)
        card.pack(expand=True, padx=40, pady=40)
        card.pack_propagate(True)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=36)

        ctk.CTkLabel(
            inner,
            text="VOLTA",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f2efe8",
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            inner,
            text="Newsletter desk · internal",
            font=ctk.CTkFont(size=14),
            text_color="#9a958c",
        ).pack(pady=(0, 24))

        self.user = ctk.CTkOptionMenu(
            inner,
            values=[m.display_name for m in STAFF.values()],
            width=280,
            height=36,
            fg_color="#2a2a2a",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a",
        )
        self.user.set("Bader")
        self.user.pack(pady=6)

        self.pin = ctk.CTkEntry(
            inner,
            placeholder_text="PIN (try 1111)",
            show="*",
            width=280,
            height=36,
            fg_color="#2a2a2a",
            border_color="#3a3a3a",
        )
        self.pin.pack(pady=6)
        self.pin.bind("<Return>", lambda _e: self._submit())

        self.error = ctk.CTkLabel(inner, text="", text_color="#e85d4c", font=ctk.CTkFont(size=12))
        self.error.pack(pady=(4, 0))

        ctk.CTkButton(
            inner,
            text="Enter desk",
            width=280,
            height=40,
            fg_color="#c45c26",
            hover_color="#a84c1e",
            command=self._submit,
        ).pack(pady=(16, 20))

        hint = "Staff PINs: Bader 1111 · Matt 2222 · Rishabh 3333 · Laura 4444 · Amy 5555"
        ctk.CTkLabel(inner, text=hint, font=ctk.CTkFont(size=11), text_color="#6e6a63").pack()

        # Focus PIN so the window is clearly interactive
        self.after(200, self.pin.focus_set)

    def _submit(self) -> None:
        name = self.user.get().strip()
        username = next((u for u, m in STAFF.items() if m.display_name == name), name.lower())
        member = authenticate(username, self.pin.get())
        if not member:
            self.error.configure(text="Wrong PIN — try again.")
            return
        self.on_success(member)
