#!/usr/bin/env python3
"""Deprecated name: use scripts/wp_sync_ml_page.py (same behavior — create or update)."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "wp_sync_ml_page.py"), run_name="__main__")
