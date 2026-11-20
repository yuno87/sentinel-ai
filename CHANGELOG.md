# Changelog

Dated changes since Milestone 1. Commit history on GitHub shows the same work.

## 2026-11-20: Milestone 2 preparation
- Reorganised the repository into the required layout: `prompts/` (v1, v2, v3, final), `code/`, `test-data/`, `docs/`.
- Turned each prompt's user message into a plain template with `{variables}`, so the prompt sheets match the code exactly.
- Added `code/tools/export_prompts.py`, which writes the 5 final prompts (P1 to P5) to `prompts/final/`.
- Saved the Milestone 1 baseline prompt as `prompts/v1/`.

## 2026-11-13: Fix for report not loading
- The page now tells the browser to always fetch the newest page files, so an old `app.js` can't call routes the server doesn't have.
- Clear "restart the server" message instead of a bare "Not Found".
- Start commands use `--reload` so the server picks up code changes.

## 2026-11-13: Usability redesign
- Three tabs: Setup, Report, Fix & re-test.
- One "Scan my chatbot" button with a live progress checklist (attacks run one by one so progress can be shown).
- Plain-English names for attack types, ⓘ tooltips for every term, a plain-language launch verdict.
- Live mode presets and a "Test connection" button.

## 2026-11-13: First working build
- Replaced the Milestone 1 single prompt with a 5-step pipeline, each step its own prompt: P1 Analyse, P2 Attacks, P3 Predict, P4 Judge, P5 Harden.
- Structured JSON output validated with Pydantic, instead of free-text lines.
- Judging moved to a separate call from the reply, with evidence quotes checked by code.
- Added a fourth attack category, prompt injection through pasted content (indirect injection), following the reviewer feedback from Milestone 1.
- Fixes split into prompt changes and application changes, plus a hardened prompt, diff view and re-test (the "mitigation" part of the Milestone 1 feedback).
- Live mode: send attacks to a real chatbot endpoint. Practice chatbot included.
- Markdown and CSV export. Demo mode for running without an API key.
- Uses Claude (Opus 5.5) for every step instead of the three models planned in Milestone 1, to keep one consistent, structured-output pipeline.

## 2026-10-09: Milestone 1 submitted
- Problem C23 chosen; single baseline prompt (now `prompts/v1/`).
