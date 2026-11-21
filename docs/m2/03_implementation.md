# 3. Implementation

## What is built

A working web app. A user pastes a chatbot's system prompt (or loads the built-in fictional travel-agency bot), picks **Simulate the replies** or **Connect my real chatbot**, and clicks **Scan my chatbot**. A progress checklist shows each step. The **Report** tab shows the launch call in plain words and a table of every attack, filterable by result and type; clicking a row shows the attack, the reply and the evidence. The **Fix & re-test** tab suggests fixes, shows the hardened prompt and what changed, and re-runs the same attacks to compare before and after. Reports download as Markdown and CSV.

Code: Python 3 (FastAPI, Pydantic, `google-genai` and `anthropic` SDKs, httpx) in `code/app/`, and a plain HTML/CSS/JavaScript page in `code/static/`. The 5 prompts are in `code/app/prompts.py`; each pipeline step is one module in `code/app/pipeline/`. 71 automated tests (pytest, using a fake model so they run offline) cover every step.

## Module status

{{module_table}}

## Prompt iteration log

{{iteration_log}}
