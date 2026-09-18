#!/usr/bin/env python3
"""Volta Newsletter — internal desk for Bader and staff (terminal UI)."""

import os
import sys
import traceback

# Quiet macOS Tk deprecation if anything still imports tk by accident
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")


def main() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()

        from app.ui.tui_app import run_app

        run_app()
    except Exception as exc:  # noqa: BLE001
        message = f"Volta Newsletter failed to start:\n\n{exc}\n\n{traceback.format_exc()}"
        print(message, file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
