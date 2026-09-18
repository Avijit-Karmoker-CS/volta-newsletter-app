#!/usr/bin/env python3
"""Volta Newsletter — internal desktop app for Bader and staff."""

from dotenv import load_dotenv

load_dotenv()

from app.ui.main_window import run_app


if __name__ == "__main__":
    run_app()
