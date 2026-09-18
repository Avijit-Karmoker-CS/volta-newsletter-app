#!/usr/bin/env python3
"""Volta Newsletter — phone & desktop web desk (optional terminal UI)."""

import argparse
import os
import sys
import traceback

os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")


def main() -> None:
    parser = argparse.ArgumentParser(description="Volta Newsletter desk")
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Run terminal UI instead of phone/desktop web app",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web bind host (default 0.0.0.0 for phone access)")
    parser.add_argument("--port", type=int, default=8000, help="Web port (default 8000)")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()

        if args.tui:
            from app.ui.tui_app import run_app

            run_app()
        else:
            from app.web.server import run_web

            run_web(host=args.host, port=args.port)
    except Exception as exc:  # noqa: BLE001
        message = f"Volta Newsletter failed to start:\n\n{exc}\n\n{traceback.format_exc()}"
        print(message, file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
