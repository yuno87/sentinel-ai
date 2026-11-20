# Sentinel AI: notes for Claude

A prompt safety tester for chatbots, built as a student project. The user pastes a chatbot system prompt; the app analyses it, generates attacks (INJ/OVR/JBK/LEAK), runs them (predicted or live), judges each reply, and suggests fixes plus a hardened prompt, with re-test and Markdown/CSV export. See README.md for the full feature list.

## Course context
SCSE4041 Prompt Engineering mini project, team Sentinel AI (Team ID PE-B49-24, problem C23). The repo layout follows the Milestone 2 guidelines: `prompts/` (v1, v2, v3, final), `code/`, `test-data/`, `docs/`, `CHANGELOG.md`. Add a dated CHANGELOG entry for notable changes. Never commit API keys.

## Stack
- Python 3.13, FastAPI + uvicorn, Pydantic v2, official `anthropic` SDK (2.x), httpx, python-dotenv, pytest.
- All code is in `code/`; front end is plain HTML/CSS/JS in `code/static/` (no framework, no build step).
- Virtualenv at the repo root, `.venv` (Windows: `.venv/Scripts/python`).

## Commands (run from `code/`)
- Tests: `../.venv/Scripts/python -m pytest -q` (offline; uses `FakeLLM` and demo mode)
- Run the app: `../.venv/Scripts/python -m uvicorn app.main:app --reload` (demo mode automatically when no key is set; real model when `code/.env` has `ANTHROPIC_API_KEY`)
- Mock live bot: `../.venv/Scripts/python -m mock_bot.server` (port 8001)
- Regenerate `prompts/final/` after changing a prompt: `../.venv/Scripts/python -m tools.export_prompts`
- Use `http://127.0.0.1`, not `localhost`, for local URLs on this Windows machine. `localhost` tries IPv6 first and adds about 2 seconds per request.

## Architecture
- `code/app/llm.py`: the ONLY place that calls Claude. `ClaudeClient.structured(task, system, user, output_model)` uses `client.beta.messages.create` with `output_config.format` (JSON schema from `to_strict_schema`), per-task `effort`, and server-side refusal fallbacks (`fallbacks="default"`, beta `server-side-fallback-2026-07-01`). Checks `stop_reason`, validates with Pydantic, and retries once. `FakeLLM` (tests) and `DemoLLM` (`app/demo.py`) have the same interface; `get_llm()` picks one.
- `code/app/prompts.py`: the 5 prompts P1-P5, each a SYSTEM string plus a USER template with {variables} filled by `.format`. Untrusted text is wrapped in XML tags.
- `app/pipeline/*`: one module per step. Each one is a pure function that takes `llm` as an argument.
- `app/main.py`: thin, stateless routes. The browser holds state and posts what each step needs.
- Page flow (`static/app.js`): three tabs (Setup, Report, Fix & re-test). "Scan my chatbot" calls `/api/analyze` and `/api/attacks`, then `/api/run` once per attack (3 in parallel, so it can show progress), then `/api/summary`. Re-test runs the same way, then `/api/compare`. `/api/live/test` backs the "Test connection" button. `/api/retest` still exists for API users but the page doesn't use it.
- UI wording is plain English (category names like "Hidden instructions", ⓘ tooltips). Exports keep the standard security terms (`CATEGORY_LABEL` in `schemas.py`).
- Demo mode turns on automatically when no API key is set (or `SENTINEL_DEMO=1`). `SENTINEL_DEMO_DELAY` (default 0.4 s) slows demo answers so the progress checklist is visible; `tests/conftest.py` sets it to 0. `tools/run_tests.py` and `tools/prompt_experiment.py` require a real key and must never report demo answers as results.
- Model: `claude-opus-5-5` (env `SENTINEL_MODEL`). Opus 5.5 can't disable thinking or use forced tool_choice, and does not support prefill.

## Deployment
- Prototype is hosted on Vercel using Services (`vercel.json`): `sentinel` (root `code/`, entrypoint `app.main:app`, public via rewrite `/(.*)`) and `practice_bot` (root `code/`, entrypoint `mock_bot.server:app`, internal). `sentinel` binds `practice_bot` as `PRACTICE_BOT_URL`; read it at call time in `live_client.practice_bot_chat_url()` (bindings exist only at runtime). Never hardcode the practice bot's address in the browser. Key is a Vercel env var. Hugging Face Spaces was dropped (compute Spaces need a paid plan).
- AI provider: Claude if ANTHROPIC_API_KEY, else Gemini (`gemini-3.5-flash-lite`) if GEMINI_API_KEY, else demo mode.

## Rules to keep
- The API key stays server-side. `/api/info` must never return it (there is a test for this).
- Predicted replies must always be labelled as predictions (UI badge + note, `reply.mode`, report banner).
- Generated attacks must not request genuinely harmful content and must only use made-up names and example.com. Keep `SAFE_CONTENT_RULES` and the `safety_problems` screen.
- Deterministic logic stays in code, not the LLM: attack IDs, launch call (`verdict.py`), diff, comparison, evidence check, Pass means severity "None".
- A failed live call is an Error (`judgment=None`), never a verdict.
- LLM output models use only simple types and enums (structured output supports a subset of JSON Schema). Put extra validation in Python.
- Code is for a student to present: keep it commented and simple. Prefer clarity over cleverness.
- Add or update a test in `tests/` for every pipeline change.
