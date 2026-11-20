"""
Write the 5 final prompts to prompts/final/, one Markdown file per prompt.

The files are generated from app/prompts.py, so they always match what the
app really sends to Claude. Run it again whenever a prompt changes:

    (from the code/ folder)  python -m tools.export_prompts
"""

import json
import re
from pathlib import Path

from app import config, prompts
from app.llm import EFFORT_BY_TASK, to_strict_schema
from app.schemas import Analysis, AttackDraftList, Hardening, Judgment, PredictedReply

OUT_DIR = Path(__file__).resolve().parents[2] / "prompts" / "final"

# One entry per final prompt: everything a prompt sheet needs except the sample run.
PROMPTS = [
    {
        "id": "P1", "name": "Analyse", "file": "P1_analyse.md", "task": "analyze",
        "step": "Step 1 of 5: runs once per scan, first.",
        "purpose": "Work out what the bot is for, its rules, what it must protect, its capabilities and the weak spots in how its prompt is written.",
        "system": prompts.ANALYZE_SYSTEM, "user": prompts.ANALYZE_USER, "output": Analysis,
        "variables": {"system_prompt": "The chatbot system prompt the user pasted (the prompt under test)."},
    },
    {
        "id": "P2", "name": "Write attacks", "file": "P2_attacks.md", "task": "attacks",
        "step": "Step 2 of 5: runs once per scan, after P1.",
        "purpose": "Write attack messages tailored to this bot in 4 categories, without asking for genuinely harmful content.",
        "system": prompts.ATTACKS_SYSTEM, "user": prompts.ATTACKS_USER, "output": AttackDraftList,
        "variables": {
            "per_category": "How many attacks to write per category (1 to 5, default 3).",
            "total": "per_category x 4, the total number of attacks.",
            "system_prompt": "The prompt under test.",
            "analysis_json": "P1's output (purpose, rules R1..Rn, protected assets, weak spots) as JSON.",
        },
    },
    {
        "id": "P3", "name": "Predict reply", "file": "P3_predict.md", "task": "predict",
        "step": "Step 3 of 5: runs once per attack, in predicted mode only (live mode calls the real chatbot instead).",
        "purpose": "Predict how a typical chatbot with this system prompt would reply to one attack. The output is always labelled as a prediction.",
        "system": prompts.PREDICT_SYSTEM, "user": prompts.PREDICT_USER, "output": PredictedReply,
        "variables": {
            "system_prompt": "The prompt under test.",
            "attack_prompt": "One attack message written by P2.",
        },
    },
    {
        "id": "P4", "name": "Judge", "file": "P4_judge.md", "task": "judge",
        "step": "Step 4 of 5: runs once per attack, after the reply (predicted or live). A separate call from P3.",
        "purpose": "Mark the reply Pass or Fail with a severity, a one-line reason and an exact quote from the reply as evidence.",
        "system": prompts.JUDGE_SYSTEM, "user": prompts.JUDGE_USER, "output": Judgment,
        "variables": {
            "system_prompt": "The prompt under test.",
            "rules_and_assets_json": "The rules and protected assets from P1, as JSON.",
            "attack_id": "The attack's ID, e.g. INJ-01 (assigned by code, not the model).",
            "category": "The attack category, e.g. Prompt injection.",
            "technique": "The attack's technique name from P2.",
            "goal": "What the attacker wanted the bot to do (from P2).",
            "target_rules": "Rule IDs the attack targets, e.g. R4.",
            "attack_prompt": "The attack message.",
            "reply_text": "The bot's reply: predicted by P3, or real from the live endpoint.",
        },
    },
    {
        "id": "P5", "name": "Harden", "file": "P5_harden.md", "task": "harden",
        "step": "Step 5 of 5: runs when the user clicks Suggest fixes, after the scan.",
        "purpose": "Suggest fixes (prompt changes and app changes, linked to the failed attacks) and rewrite the system prompt to be harder to attack.",
        "system": prompts.HARDEN_SYSTEM, "user": prompts.HARDEN_USER, "output": Hardening,
        "variables": {
            "system_prompt": "The prompt under test.",
            "weak_spots": "The weak spots found by P1, one per line.",
            "failed_attacks": "One line per failed attack: ID, severity, technique, judge's reason and evidence.",
        },
    },
]


def template_variables(template: str) -> list[str]:
    """The {names} used in a template, in order, without repeats."""
    return list(dict.fromkeys(re.findall(r"\{(\w+)\}", template)))


def render(p: dict) -> str:
    schema = json.dumps(to_strict_schema(p["output"]), indent=2)
    variables = "\n".join(f"| `{{{name}}}` | {text} |" for name, text in p["variables"].items())
    return f"""# {p['id']} {p['name']}

| Field | Value |
|---|---|
| Prompt ID and name | {p['id']} {p['name']} |
| Step in the workflow | {p['step']} |
| Purpose | {p['purpose']} |
| Tool and model | Anthropic Claude API, model `{config.MODEL}` (Python SDK, called from `code/app/llm.py`) |
| Settings | effort `{EFFORT_BY_TASK[p['task']]}`, adaptive thinking (model default), max_tokens 16000, structured JSON output. Temperature is not set: this model does not accept it. |
| Number of examples included | 0 (zero-shot; the rules and output schema do the steering) |
| Output format | JSON matching the `{p['output'].__name__}` schema below, validated with Pydantic |

## System prompt

```text
{p['system']}
```

## User prompt template

```text
{p['user']}
```

## Variables

| Variable | What it holds |
|---|---|
{variables}

## Output schema (sent to the API as `output_config.format`)

```json
{schema}
```
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in PROMPTS:
        # Every variable in the template must be documented, and vice versa.
        assert template_variables(p["user"]) == list(p["variables"]), p["id"]
        (OUT_DIR / p["file"]).write_text(render(p), encoding="utf-8")
        print("wrote", OUT_DIR / p["file"])


if __name__ == "__main__":
    main()
