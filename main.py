#!/usr/bin/env python3
"""Volta Newsletter — internal desktop app for Bader and staff."""

import sys
import traceback


def main() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()

        from app.ui.main_window import run_app

        run_app()
    except Exception as exc:  # noqa: BLE001 — show startup errors to the user
        message = f"Volta Newsletter failed to start:\n\n{exc}\n\n{traceback.format_exc()}"
        print(message, file=sys.stderr)
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Volta Newsletter", message)
            root.destroy()
        except Exception:
            pass
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
