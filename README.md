# Sentinel AI: A Prompt Safety Tester for Chatbots

**A red-team kit that helps teams find security weaknesses in their chatbots before launch.**

SCSE4041 Prompt Engineering, Mini Project · Team **Sentinel AI** (Team ID PE-B49-24) · Problem Pool **C23** Prompt safety tester (red-team kit)

| | |
|---|---|
| Prototype | _link added after deployment_ |
| Repository | _this repository_ |
| Reel | _link added after recording_ |

## Team

| Member | Enrollment no. |
|---|---|
| Ayanna Tyagi (leader) | S24CSEU0125 |
| Atharv Arora | S24CSEU2439 |
| Karan Singh Saggu | S24CSEU1939 |
| Jatin Khanchi | S24CSEU1932 |

Faculty: Ankit Vijay Bansal

---

## What it does

Paste a chatbot's system prompt. Sentinel AI:

1. **Analyses** it: purpose, rules, what it must protect, its capabilities, and weak spots in how the prompt is written.
2. **Generates attacks** tailored to that bot in four categories: prompt injection (`INJ`), instruction override (`OVR`), jailbreak (`JBK`) and system prompt leak (`LEAK`).
3. **Runs** them in one of two modes:
   - **Predicted** (baseline): Claude predicts how a typical bot with this prompt would reply. These are always labelled as predictions, never as real results.
   - **Live**: sends each attack to your real chatbot over HTTP and records the real reply.
4. **Judges** every reply as Pass or Fail with a severity (Critical / High / Medium / Low / None) and a quoted piece of evidence, using a separate Claude call.
5. **Reports**: a filterable results table, an overall launch call, suggested fixes (prompt changes and application changes), and a hardened prompt with a diff.
6. **Re-tests** the hardened prompt and shows what was fixed, what still fails, and any new failures. It can also start a fresh scan of the hardened prompt with new attacks.
7. **Exports** the report as Markdown and the table as CSV.

> Attacks test whether a bot breaks its *own* rules (leaking a discount code, sharing another customer's booking). They never ask for genuinely harmful content, and they use only made-up names and `example.com` addresses.

---

## Repository layout

```
README.md         this file
CHANGELOG.md      dated list of changes since Milestone 1
prompts/
  v1/             Milestone 1 baseline prompt
  v2/, v3/        later prompt versions (iteration log)
  final/          the 5 final prompts, one file each (P1 to P5)
code/             the app (Python + a plain HTML/JS page)
test-data/        inputs used in the test table, and saved outputs
docs/             diagrams, supporting document, Milestone 2 PDF
```

---

## Setup

You need **Python 3.10+**. From the `sentinel` folder:

```bash
python -m venv .venv
```

Activate the virtual environment:

- Windows (Command Prompt): `.venv\Scripts\activate.bat`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

Once it's active, your prompt starts with `(.venv)`. Command Prompt needs backslashes in paths; forward slashes fail with "'.venv' is not recognized".

Then go into the `code` folder and install the dependencies. **All commands below run from `code/`.**

```bash
cd code
pip install -r requirements.txt
```

No API key is needed.

---

## Run

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>, click **Try the example bot**, then **Scan my chatbot**.

**This prototype runs in demo mode.** With no API key set, Sentinel plays back pre-written answers for the built-in example bot, so the whole flow works for free with no setup. The page header says **Demo mode**, and exported reports are marked as demo data. Demo mode only works with the built-in example prompt, and its answers are pre-written, not real model output.

### Using a real AI model

Add **one** key to `code/.env` (copy `code/.env.example`), and Sentinel uses that AI automatically:

| Key | Model | Cost |
|---|---|---|
| `GEMINI_API_KEY` from <https://aistudio.google.com/apikey> | Gemini 3.5 Flash-Lite | free (with daily limits) |
| `ANTHROPIC_API_KEY` from <https://console.anthropic.com> | Claude Opus 5.5 | paid |

Keys are only read by the Python server, are never sent to the browser, and `.env` is ignored by git. On a free Gemini key, Sentinel waits and retries automatically when Google's per-minute limit is hit, so a scan can take a few minutes. The test runner (`tools/run_tests.py`) and the prompt experiment (`tools/prompt_experiment.py`) need a key, because their results must be real model output.

### Using the app

The page has three tabs:

1. **Setup**: paste a system prompt, choose *Simulate the replies* or *Connect my real chatbot*, and click **Scan my chatbot**. A checklist shows progress ("Testing the attacks 7 of 12"). Under *More options* you can change how many attacks to write, or review the attacks before they run.
2. **Report**: the overall verdict in plain words, then every attack with Pass/Fail and severity. Use the chips to filter, and click a row to see the attack and the reply. Hover over any ⓘ for an explanation of a term.
3. **Fix & re-test**: get suggested fixes and a stronger prompt (with a "what changed" view and a Copy button), re-test it against the same attacks, or start a fresh scan of the fixed prompt with new attacks.

### Trying live mode

A deliberately weak practice chatbot is included. Start it in a second terminal (also from `code/`):

```bash
python -m mock_bot.server
```

Then in Setup pick **Connect my real chatbot**. The *Sentinel's practice bot* preset is already selected, so click **Test connection** to check it, then **Scan my chatbot**.

For your own bot, pick the preset closest to its API and fill in the web address. *Request format (advanced)* lets you change:

| Field | Example |
|---|---|
| Web address (URL) | `https://my-bot.example.com/chat` |
| Extra headers (JSON) | `{"Authorization": "Bearer my-test-token"}` |
| Message to send (JSON) | `{"messages": [{"role": "user", "content": "{{attack}}"}]}` |
| Where the answer is | `choices.0.message.content` |

`{{system_prompt}}` can also be used in the message if your bot accepts its prompt per request. Only test chatbots you own or are allowed to test.

### Tests and prompt files

```bash
python -m pytest
python -m tools.export_prompts
```

The tests use a fake LLM and demo mode, so they run offline and cost nothing. `export_prompts` regenerates `prompts/final/` from `code/app/prompts.py`.

---

## How it works

```
 browser (code/static/)            server (code/app/)                    Claude API
 ──────────────────────            ──────────────────                    ──────────
 paste prompt   ── /api/analyze ─► P1 analyse ─────────── structured JSON ─► Gemini or Claude
                ── /api/attacks ─► P2 attacks  (IDs + safety screen in code)
 per attack     ── /api/run ─────► P3 predict (or live HTTP call to your bot)
                                   └► P4 judge (separate call)
                ── /api/summary ─► launch call (plain code)
 fix            ── /api/harden ──► P5 harden (+ difflib diff)
 re-test        ── /api/run, /api/compare
 export         ── /api/export ──► Markdown / CSV
```

Design choices:

- **Structured output plus validation.** Each step's output is a Pydantic class (`code/app/schemas.py`). Its JSON Schema is sent to Claude and the reply is validated against the same class. An invalid reply is retried once, then reported as an error.
- **Code does what code can do.** Attack IDs, the launch call, the diff and the before/after comparison are plain Python, not LLM output.
- **The judge is checked too.** The code verifies that the judge's evidence quote really appears in the reply, and that a Pass always has severity None.
- **Separate calls.** The predicted reply and the verdict come from different calls with different system prompts.
- **Errors are not verdicts.** If a live endpoint fails, that attack shows as *Error*, never as a Pass or Fail.

### Launch call rules

| Worst failure | Launch call |
|---|---|
| Any Critical | Block launch |
| Any High | Hold launch |
| Any Medium or Low | Fix before launch |
| None | No failures found |
| No attack could be judged (all errored) | Not tested |

### Limitations

- Predicted mode is an estimate. A real bot may be stronger or weaker, so use live mode before launch.
- The re-test uses attacks the hardening step has already seen, so passing them is easier than passing new ones. Start a fresh scan of the fixed prompt for a fair test.
- Attacks are single messages. Multi-turn attacks are not covered.
- A full scan of 12 attacks makes about 26 Claude calls.

---

## Deployment (prototype link)

The prototype is hosted on **Vercel** (free Hobby plan), deployed straight from this GitHub repository, using Vercel **Services** (`vercel.json`):

| Service | Code | Public? |
|---|---|---|
| `sentinel` | `code/app/main.py` (`app`) | Yes: every path (`/`, `/api/...`, `/static/...`) |
| `practice_bot` | `code/mock_bot/server.py` (`app`) | No: internal only |

- `sentinel` has a **binding** to `practice_bot`: Vercel injects the practice bot's internal address into `PRACTICE_BOT_URL` at runtime. When live mode uses "Sentinel's practice bot", the browser sends no address and the server reads `PRACTICE_BOT_URL` (falling back to `http://127.0.0.1:8001/` locally).
- The AI key is set in Vercel under **Settings → Environment Variables** as `GEMINI_API_KEY`, never in the repository.
- A `Dockerfile` is also included to run the app in any container host: `docker build -t sentinel-ai .` then `docker run -p 7860:7860 -e GEMINI_API_KEY=... sentinel-ai`.

## Code structure

```
code/
  app/
    main.py            FastAPI routes and the web page
    config.py          settings from environment variables
    llm.py             Claude wrapper, schema conversion, fake LLM for tests
    schemas.py         every data model (Pydantic)
    prompts.py         the 5 prompts (P1 to P5)
    examples.py        the built-in fictional chatbot
    demo.py            pre-written answers for demo mode
    live_client.py     live-mode HTTP calls
    export.py          Markdown and CSV export
    pipeline/          analyze, attacks, runner, judge, verdict, harden, retest
  mock_bot/server.py   deliberately weak practice chatbot
  static/              index.html, app.js, styles.css (no build step)
  tests/               pytest tests for every step
  tools/               export_prompts.py
```
