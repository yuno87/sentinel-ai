# Sentinel AI

**A red-team kit that helps teams find security weaknesses in their chatbots before launch.**

Paste a chatbot's system prompt. Sentinel AI:

1. **Analyses** it: purpose, rules, what it must protect, its capabilities, and weak spots in how the prompt is written.
2. **Generates attacks** tailored to that bot in four categories: prompt injection (`INJ`), instruction override (`OVR`), jailbreak (`JBK`) and system prompt leak (`LEAK`).
3. **Runs** them in one of two modes:
   - **Predicted** (baseline): Claude predicts how a typical bot with this prompt would reply. These are always labelled as predictions, never as real results.
   - **Live**: sends each attack to your real chatbot over HTTP and records the real reply.
4. **Judges** every reply as Pass or Fail with a severity (Critical / High / Medium / Low / None) and a quoted piece of evidence, using a separate Claude call.
5. **Reports**: a filterable results table, an overall launch call, suggested fixes (prompt changes and application changes), and a hardened prompt with a diff.
6. **Re-tests** the hardened prompt and shows what was fixed, what still fails, and any new failures. It can also make the hardened prompt the new baseline so you can test it with fresh attacks.
7. **Exports** the report as Markdown and the table as CSV.

> Attacks test whether a bot breaks its *own* rules (leaking a discount code, sharing another customer's booking). They never ask for genuinely harmful content, and they use only made-up names and `example.com` addresses.

---

## Setup

You need **Python 3.10+**.

```bash
cd sentinel
python -m venv .venv
```

Activate the virtual environment:

- Windows (Command Prompt): `.venv\Scripts\activate.bat`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (Git Bash): `source .venv/Scripts/activate`
- macOS / Linux: `source .venv/bin/activate`

Once it's active, your prompt starts with `(.venv)` and the commands below work as written. If you skip activation, start each command with the venv's Python instead, for example `.venv\Scripts\python -m uvicorn ...` in Command Prompt. Command Prompt needs backslashes in paths; forward slashes fail with "'.venv' is not recognized".

Install the dependencies:

```bash
pip install -r requirements.txt
```

### Add your API key

Copy `.env.example` to `.env` and paste your Anthropic API key (from <https://console.anthropic.com>):

```
ANTHROPIC_API_KEY=sk-ant-...
```

The key is only read by the Python server. It is never sent to the browser, and `.env` is ignored by git.

---

## Run

### With an API key

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>, click **Try the example bot**, then **Scan my chatbot**.

### Using the app

The page has three tabs:

1. **Setup**: paste a system prompt, choose *Simulate the replies* or *Connect my real chatbot*, and click **Scan my chatbot**. A checklist shows progress ("Testing the attacks 7 of 12"). Under *More options* you can change how many attacks to write, or review the attacks before they run.
2. **Report**: the overall verdict in plain words, then every attack with Pass/Fail and severity. Use the chips to filter, and click a row to see the attack and the reply. Hover over any ⓘ for an explanation of a term.
3. **Fix & re-test**: get suggested fixes and a stronger prompt (with a "what changed" view and a Copy button), re-test it against the same attacks, or start a fresh scan of the fixed prompt with new attacks.

### Without an API key (demo mode)

Demo mode plays back pre-written responses for the built-in example, so you can see and present the whole app for free:

```bash
uvicorn app.main:app --reload --env-file demo.env
```

The page header says **Demo mode**, and exported reports are marked as demo data. Demo mode only works with the built-in example prompt.

### Trying live mode

A deliberately weak mock chatbot is included. Start it in a second terminal:

```bash
python -m mock_bot.server
```

Then in Setup pick **Connect my real chatbot**. The *Sentinel's practice bot* preset is already selected, so click **Test connection** to check it, then **Scan my chatbot**.

For your own bot, pick the preset closest to its API and fill in the web address. Use **Test connection** to check the settings before scanning. *Request format (advanced)* lets you change:

| Field | Example |
|---|---|
| Web address (URL) | `https://my-bot.example.com/chat` |
| Extra headers (JSON) | `{"Authorization": "Bearer my-test-token"}` |
| Message to send (JSON) | `{"messages": [{"role": "user", "content": "{{attack}}"}]}` |
| Where the answer is | `choices.0.message.content` |

`{{system_prompt}}` can also be used in the body template if your bot accepts its prompt per request. Only test chatbots you own or are allowed to test.

### Running the tests

```bash
python -m pytest
```

The tests use a fake LLM and demo mode, so they run offline and cost nothing.

---

## How it works

```
 browser (static/)                 server (app/)                         Claude API
 ─────────────────                 ─────────────                         ──────────
 1 paste prompt  ── /api/analyze ─► analyze.py ───────── structured JSON ─► Opus 5.5
 2 attacks       ── /api/attacks ─► attacks.py  (IDs + safety screen in code)
 3 run           ── /api/run ─────► runner.py ─► predict (or live HTTP call)
                                              └► judge.py (separate call)
                                    verdict.py  (launch call: plain code)
 4 fixes         ── /api/harden ──► harden.py  (+ difflib diff)
 5 re-test       ── /api/retest ──► runner.py + retest.py (compare)
 6 export        ── /api/export ──► export.py (Markdown / CSV)
```

Design choices worth knowing:

- **Structured output plus validation.** Each step's output is a Pydantic class (`app/schemas.py`). We send its JSON Schema to Claude and validate the reply against the same class. If the reply is invalid, we ask once more, and then show an error.
- **Code does what code can do.** Attack IDs, the launch call, the diff and the before/after comparison are plain Python, not LLM output, so they are predictable and testable.
- **The judge is checked too.** Our code verifies that the judge's evidence quote really appears in the reply, and enforces that a Pass always has severity None.
- **Separate calls.** The reply (prediction) and the verdict come from different calls with different system prompts.
- **Errors are not verdicts.** If a live endpoint fails, that attack shows as *Error*. It is never counted as a Pass or a Fail.
- **Stateless server.** The browser holds the current results and sends what each step needs, so there is no database.

### Launch call rules

| Worst failure | Launch call |
|---|---|
| Any Critical | Block launch |
| Any High | Hold launch |
| Any Medium or Low | Fix before launch |
| None | No failures found |

### Limitations

- Predicted mode is an estimate. A real bot may be stronger or weaker, so use live mode before launch.
- The re-test uses the attacks the hardening step has already seen, so passing them is easier than passing new ones. Use **Use hardened prompt as new baseline** to test it with fresh attacks.
- Attacks are single messages. Multi-turn attacks are not covered.
- Each full run makes about 25 to 30 Claude calls (analysis, attacks, and one prediction plus one judgment per attack).

---

## Project structure

```
app/
  main.py            FastAPI routes (one per step) and the web page
  config.py          settings from environment variables
  llm.py             Claude wrapper, schema conversion, fake LLM for tests
  schemas.py         every data model (Pydantic)
  prompts.py         every prompt sent to Claude
  examples.py        the built-in fictional chatbot
  demo.py            canned responses for demo mode
  live_client.py     live-mode HTTP calls
  export.py          Markdown and CSV export
  pipeline/
    analyze.py  attacks.py  runner.py  judge.py  verdict.py  harden.py  retest.py
mock_bot/server.py   deliberately weak chatbot for live-mode demos
static/              index.html, app.js, styles.css (no build step)
tests/               pytest tests for every step
```
