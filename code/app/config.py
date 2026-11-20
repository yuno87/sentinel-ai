"""
Configuration for Sentinel AI.

All settings come from environment variables (or a `.env` file in the project
root). Keeping them here means the rest of the code never reads `os.environ`
directly, which makes it easy to see every setting in one place.

API keys are read here and used only by the Python server. They are never
sent to the browser.

Which AI the app uses is decided by which key is set (first match wins):
    ANTHROPIC_API_KEY  -> Claude  (paid)
    GEMINI_API_KEY     -> Gemini  (free key from Google AI Studio)
    neither            -> demo mode (pre-written answers, no AI calls)
"""

import os

from dotenv import load_dotenv

# Load variables from .env if the file exists. Real environment variables win.
load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()

# One model per provider, used for every step.
CLAUDE_MODEL: str = os.getenv("SENTINEL_MODEL", "claude-opus-5-5").strip()
# Gemini 3.5 Flash-Lite: a stable model that free API keys can use.
GEMINI_MODEL: str = os.getenv("SENTINEL_GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

_force_demo = os.getenv("SENTINEL_DEMO", "0").strip() in ("1", "true", "yes")
if _force_demo:
    PROVIDER = "demo"
elif ANTHROPIC_API_KEY:
    PROVIDER = "claude"
elif GEMINI_API_KEY:
    PROVIDER = "gemini"
else:
    PROVIDER = "demo"

# The model actually in use (shown on the page and in reports).
MODEL: str = {"claude": CLAUDE_MODEL, "gemini": GEMINI_MODEL}.get(PROVIDER, "demo")

# Demo mode plays back pre-written answers for the built-in example bot, so the
# app works with no key at all. Nothing in demo mode calls an AI.
DEMO_MODE: bool = PROVIDER == "demo"

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
