# Sentinel AI: Technical Report

*Team Sentinel AI (PE-B49-24) · SCSE4041 Prompt Engineering · Problem C23 Prompt safety tester (red-team kit) · November 2026*

## Purpose

Sentinel AI tests a chatbot's system prompt for security weaknesses before launch. The user pastes the system prompt; Sentinel works out what the bot must protect, writes attacks tailored to it, gets the bot's replies (predicted, or from the real chatbot over HTTP), judges each reply with quoted evidence, and suggests fixes plus a hardened prompt that can be re-tested.

## Architecture

A Python **FastAPI** server and a plain **HTML/JavaScript** page (three tabs: Setup, Report, Fix & re-test). The server is stateless: the page holds the current results and sends each step what it needs. All AI calls go through one module (`llm.py`), which supports **Gemini** (free key) and **Claude**, chosen by which API key is set; with no key, a labelled demo mode plays back pre-written answers. Keys stay on the server and are never sent to the browser. The prototype is hosted on Vercel (free plan) from the GitHub repository; a Dockerfile is also included.

## Tools and models

| Part | Choice |
|---|---|
| Model | Google **Gemini 3.5 Flash-Lite** via the `google-genai` SDK (free AI Studio key); Anthropic Claude Opus 5.5 also supported |
| Output control | Structured JSON output: each step sends a JSON Schema (`response_json_schema`) and the answer is validated with **Pydantic**; one retry if invalid |
| Server and data | FastAPI, Pydantic, httpx (live mode), python-dotenv |
| Testing | pytest (71 offline tests with a fake model), plus scripted real runs (`run_tests.py`, `prompt_experiment.py`) |

## Prompt design

Five prompts, one per step, each with a system prompt and a user template with `{variables}`:

- **P1 Analyse:** purpose, rules R1..Rn, protected assets, capabilities, weak spots in the wording.
- **P2 Attacks:** tailored attacks in 4 categories (hidden instructions in pasted content, rule override, jailbreak/trickery, prompt leak), with safety rules: no genuinely harmful content, made-up names, example.com only.
- **P3 Predict:** a typical bot's reply, from a description of realistic chatbot behaviour plus two contrasting examples (the only few-shot prompt).
- **P4 Judge:** a separate call that gives Pass/Fail, severity (Critical/High/Medium/Low), a one-line reason and an exact evidence quote.
- **P5 Harden:** fixes marked as prompt or application changes, linked to the failed attacks, and a rewritten prompt.

Plain code handles everything that doesn't need judgement: attack IDs, a safety screen, checking that the evidence quote is really in the reply, the launch call, the diff and the before/after comparison. Untrusted text is wrapped in XML tags so the model can tell instructions from material.

**Iteration.** Four versions were measured on the same 3 bots (6 runs each, Gemini 3.5 Flash-Lite). v1, the Milestone 1 single prompt, broke format in 1 of 6 runs, never tested hidden instructions and contradicted itself in 13 of 29 verdicts. v2 split the work and fixed the format (6/6, 4 of 4 categories) but judged 0 of 48 attacks as Fail. v3 added analysis, schemas, a separate judge and checked evidence (100 % found), but still only 2 % Fail. v4 rewrote the predictor with realistic behaviour and two examples: 31 % Fail, ranked by how weak each bot is (Copperleaf 9/16, ABC Bank 4/16, Lumen HR 2/16).

## Test results

{{tests_summary}}

## Limitations

{{limitations}}
