"""Root desktop window — not a web frontend."""

from __future__ import annotations

import customtkinter as ctk

from app.services.staff import StaffMember
from app.ui.customize import CustomizeFrame
from app.ui.home import HomeFrame
from app.ui.login import LoginFrame
from app.ui.recommendations import RecommendationsFrame
from app.ui.review import ReviewFrame


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class VoltaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Volta Newsletter")
        self.geometry("980x720")
        self.minsize(860, 640)
        self.configure(fg_color="#121212")

        self.user: StaffMember | None = None
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self._frame = None
        self.show_login()

    def _swap(self, frame) -> None:
        if self._frame is not None:
            self._frame.destroy()
        self._frame = frame
        self._frame.pack(fill="both", expand=True)

    def show_login(self) -> None:
        self._swap(LoginFrame(self.container, on_success=self._logged_in))

    def _logged_in(self, user: StaffMember) -> None:
        self.user = user
        self.show_home()

    def show_home(self, refresh: bool = False) -> None:  # noqa: ARG002
        assert self.user is not None
        self._swap(HomeFrame(self.container, self.user, navigate=self.navigate))

    def navigate(self, screen: str, **kwargs) -> None:
        assert self.user is not None
        if screen == "home" or kwargs.get("refresh"):
            self.show_home()
            if screen == "home":
                return
        if screen == "customize":
            self._swap(
                CustomizeFrame(
                    self.container,
                    self.user,
                    on_back=self.show_home,
                    on_draft_ready=lambda draft: self.navigate("review", draft=draft),
                )
            )
        elif screen == "recommendations":
            self._swap(
                RecommendationsFrame(self.container, self.user, on_back=self.show_home)
            )
        elif screen == "review":
            draft = kwargs.get("draft")
            self._swap(ReviewFrame(self.container, self.user, draft, on_back=self.show_home))
        else:
            self.show_home()


def run_app() -> None:
    app = VoltaApp()
    app.mainloop()
