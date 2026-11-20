"""
Configuration for Sentinel AI.

All settings come from environment variables (or a `.env` file in the project
root). Keeping them here means the rest of the code never reads `os.environ`
directly, which makes it easy to see every setting in one place.

The API key is read here and passed to the Anthropic client on the server.
It is never sent to the browser.
"""

import os

from dotenv import load_dotenv

# Load variables from .env if the file exists. Real environment variables win.
load_dotenv()

# The Anthropic SDK reads ANTHROPIC_API_KEY itself; we only check if it is set
# so we can show a helpful error message instead of a stack trace.
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()

# One model for every step. Opus 5.5 is the current default Claude model.
MODEL: str = os.getenv("SENTINEL_MODEL", "claude-opus-5-5").strip()

# Demo mode plays back pre-written answers for the built-in example bot, so the
# app works without an API key. Nothing in demo mode calls Claude.
# It turns on automatically when no API key is set, or when SENTINEL_DEMO=1.
DEMO_MODE: bool = (
    os.getenv("SENTINEL_DEMO", "0").strip() in ("1", "true", "yes")
    or not ANTHROPIC_API_KEY
)

# Seconds each demo answer waits, so the progress checklist is visible.
DEMO_DELAY_SECONDS: float = float(os.getenv("SENTINEL_DEMO_DELAY", "0.4") or 0)

# How many attacks to generate per category (the UI can override this).
DEFAULT_ATTACKS_PER_CATEGORY: int = 3
MAX_ATTACKS_PER_CATEGORY: int = 5

# How many attacks we run at the same time. A small number keeps us well
# under API rate limits while still being much faster than one at a time.
MAX_PARALLEL_ATTACKS: int = 4

# Timeout (seconds) when calling a user's live chatbot endpoint.
LIVE_TIMEOUT_SECONDS: float = 30.0

# Longest system prompt we accept (characters). Stops accidental huge pastes.
MAX_SYSTEM_PROMPT_CHARS: int = 30_000
