"""
Entry point for Vercel (the hosting service for the prototype link).

Vercel looks for a file named index.py at the project root that defines a
FastAPI `app`. The real app lives in code/app/, so this file just puts the
code/ folder on Python's import path and re-exports the app from there.

The AI key is set in Vercel's project settings (Environment Variables:
GEMINI_API_KEY), never in this repository. Without it the app runs in demo mode.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "code"))

from app.main import app  # noqa: E402  (must come after the path change)

__all__ = ["app"]
