# 2. Prompt and solution design

## 2(a) Design summary

**Problem and users.** Teams that put a customer-facing chatbot live usually write its system prompt and ship it without testing how it behaves under attack. Prompt injection is the top risk in the OWASP Top 10 for LLM Applications (LLM01). Attackers can override the bot's instructions, extract hidden secrets or other users' data, or leak the prompt itself. Sentinel AI is for the developers and prompt engineers who build these bots: it gives them a red-team test of their prompt before launch, with results in plain language and concrete fixes.

**Input and output.** *Input:* the chatbot's system prompt and, optionally, the web address of the real chatbot. *Output:* an evaluation table (attack, category, Pass/Fail, severity, one-line reason, evidence quoted from the reply), an overall launch call (Block launch / Hold launch / Fix before launch / No failures found / Not tested), suggested fixes marked as prompt or application changes and linked to the attacks they fix, a hardened system prompt with a view of what changed, a before/after re-test, and Markdown and CSV exports.

**How many prompts and why.** The final solution uses **5 prompts**, each one LLM call with one job:

| ID | Prompt | Why it is a separate step |
|---|---|---|
| P1 | Analyse | Attacks are only useful if they target this bot's real rules and secrets, so the bot is understood first (rules R1..Rn, protected assets, weak spots). |
| P2 | Write attacks | Needs P1's analysis; has its own safety rules (no genuinely harmful content, made-up names, example.com only). |
| P3 | Predict reply | Simulates a typical chatbot with the prompt. Replaced by a real HTTP call in live mode. |
| P4 | Judge | Kept separate from P3 so the judge never grades its own prediction; must quote evidence that the code then checks. |
| P5 | Harden | Writes fixes and a new prompt from the failures; runs only when the user asks. |

Everything that doesn't need judgement is plain code, not an LLM call: attack IDs, a safety screen on attack text, the evidence check, the launch call, the diff and the before/after comparison. That makes those parts predictable and testable.

**Tool and model, and why.** A Python web app (FastAPI server, plain HTML/JS page) calling **Google Gemini 3.5 Flash-Lite** through the official `google-genai` SDK. We chose it because it is a stable model that a **free** AI Studio key can use, and it supports **structured JSON output**: each prompt sends a JSON Schema and the answer is validated with Pydantic, which removed the parsing problems we saw with free-text output (see the iteration log). The same prompts also run unchanged on Anthropic Claude (Opus 5.5) when that key is set. Without any key the app runs a clearly labelled demo mode.

**What changed since Milestone 1.**

- One prompt became a **5-step pipeline** (P1 to P5) with code steps in between.
- Free-text `|`-separated lines became **structured JSON** validated against a schema.
- Added **indirect prompt injection** (instructions hidden in pasted emails and reviews) as a fourth attack category, and **mitigation** (fixes, hardened prompt, re-test), following the Cybersecurity Engineer's feedback on Milestone 1.
- Judging became a **separate call** with an **evidence quote** checked by code.
- Added **live mode** to test a real chatbot endpoint, not only predictions.
- We had planned to use ChatGPT, Gemini and Claude. We built on **one model at a time** (Gemini for Milestone 2; Claude supported) to keep a consistent, structured-output pipeline. Comparing models is planned for Milestone 3.

## 2(b) Diagrams

All four diagrams are drawn from `code/tools/make_diagrams.py` and match the built system.

{{diagram:prompt_workflow}}

{{diagram:task_decomposition}}

{{diagram:input_output_flow}}

{{diagram:system_architecture}}

No agent loop or retrieval (RAG) is used, so no agent or RAG diagram is included.

{{prompt_sheets}}
