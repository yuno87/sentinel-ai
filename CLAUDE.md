# Sentinel AI: notes for Claude

A prompt safety tester for chatbots, built as a student project. The user pastes a chatbot system prompt; the app analyses it, generates attacks (INJ/OVR/JBK/LEAK), runs them (predicted or live), judges each reply, and suggests fixes plus a hardened prompt, with re-test and Markdown/CSV export. See README.md for the full feature list.

## Stack
- Python 3.13, FastAPI + uvicorn, Pydantic v2, official `anthropic` SDK (2.x), httpx, python-dotenv, pytest.
- Front end: plain HTML/CSS/JS in `static/` (no framework, no build step).
- Virtualenv at `.venv` (Windows: `.venv/Scripts/python`).

## Commands
- Tests: `.venv/Scripts/python -m pytest -q` (offline; uses `FakeLLM` and demo mode)
- Run with API key: `.venv/Scripts/python -m uvicorn app.main:app --reload`
- Run without key: `.venv/Scripts/python -m uvicorn app.main:app --env-file demo.env`
- Mock live bot: `.venv/Scripts/python -m mock_bot.server` (port 8001)
- Use `http://127.0.0.1`, not `localhost`, for local URLs on this Windows machine. `localhost` tries IPv6 first and adds about 2 seconds per request.

## Architecture
- `app/llm.py`: the ONLY place that calls Claude. `ClaudeClient.structured(task, system, user, output_model)` uses `client.beta.messages.create` with `output_config.format` (JSON schema from `to_strict_schema`), per-task `effort`, and server-side refusal fallbacks (`fallbacks="default"`, beta `server-side-fallback-2026-07-01`). Checks `stop_reason`, validates with Pydantic, and retries once. `FakeLLM` (tests) and `DemoLLM` (`app/demo.py`) have the same interface; `get_llm()` picks one.
- `app/prompts.py`: every prompt. Untrusted text is wrapped in XML tags.
- `app/pipeline/*`: one module per step. Each one is a pure function that takes `llm` as an argument.
- `app/main.py`: thin, stateless routes. The browser holds state and posts what each step needs.
- Page flow (`static/app.js`): three tabs (Setup, Report, Fix & re-test). "Scan my chatbot" calls `/api/analyze` and `/api/attacks`, then `/api/run` once per attack (3 in parallel, so it can show progress), then `/api/summary`. Re-test runs the same way, then `/api/compare`. `/api/live/test` backs the "Test connection" button. `/api/retest` still exists for API users but the page doesn't use it.
- UI wording is plain English (category names like "Hidden instructions", ⓘ tooltips). Exports keep the standard security terms (`CATEGORY_LABEL` in `schemas.py`).
- `SENTINEL_DEMO_DELAY` (set in `demo.env`) slows demo answers so the progress checklist is visible. Keep it 0 in tests.
- Model: `claude-opus-5-5` (env `SENTINEL_MODEL`). Opus 5.5 can't disable thinking or use forced tool_choice, and does not support prefill.

## Rules to keep
- The API key stays server-side. `/api/info` must never return it (there is a test for this).
- Predicted replies must always be labelled as predictions (UI badge + note, `reply.mode`, report banner).
- Generated attacks must not request genuinely harmful content and must only use made-up names and example.com. Keep `SAFE_CONTENT_RULES` and the `safety_problems` screen.
- Deterministic logic stays in code, not the LLM: attack IDs, launch call (`verdict.py`), diff, comparison, evidence check, Pass means severity "None".
- A failed live call is an Error (`judgment=None`), never a verdict.
- LLM output models use only simple types and enums (structured output supports a subset of JSON Schema). Put extra validation in Python.
- Code is for a student to present: keep it commented and simple. Prefer clarity over cleverness.
- Add or update a test in `tests/` for every pipeline change.
