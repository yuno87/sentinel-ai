"""
Write the "one sample run" part of each prompt sheet from SAVED REAL outputs.

Nothing is invented and no AI is called: the inputs and outputs are copied
from test-data/outputs/ (P1-P4 from test T01, P5 from test T07).

Run from the code/ folder:  python -m tools.make_sample_runs
Output: docs/m2/sample_runs/P1.md ... P5.md
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "test-data" / "outputs"
OUT = ROOT / "docs" / "m2" / "sample_runs"


def load(test_id: str) -> dict:
    return json.loads((OUTPUTS / f"{test_id}.json").read_text(encoding="utf-8"))


def block(text: str, lang: str = "text") -> str:
    return f"```{lang}\n{text}\n```"


def js(obj) -> str:
    """
    JSON laid out compactly for the report: one top-level field per line, and
    lists with one item per line. Same content as json.dumps, fewer lines.
    """
    if not isinstance(obj, dict):
        return json.dumps(obj, ensure_ascii=False)
    lines = []
    for key, value in obj.items():
        if isinstance(value, list) and value:
            items = ",\n    ".join(json.dumps(v, ensure_ascii=False) for v in value)
            lines.append(f'  "{key}": [\n    {items}\n  ]')
        else:
            lines.append(f'  "{key}": {json.dumps(value, ensure_ascii=False)}')
    return "{\n" + ",\n".join(lines) + "\n}"


def shorten_list(items: list, keep: int, what: str) -> list:
    """Keep the first few items and add a clear marker saying how many were left out."""
    if len(items) <= keep:
        return items
    return items[:keep] + [f"... {len(items) - keep} more {what} (shortened for the report)"]


def shorten_text(text: str, keep_lines: int, max_chars: int = 500) -> str:
    """Keep the start of a long text (by lines and by length) and say how much was left out."""
    lines = text.strip().splitlines()
    kept = "\n".join(lines[:keep_lines])
    if len(kept) > max_chars:
        kept = kept[:max_chars].rsplit(" ", 1)[0]
    left_out = len(text.strip()) - len(kept)
    if left_out <= 0:
        return text
    return f"{kept} ... [{left_out} more characters, shortened for the report]"


def write(pid: str, body: str) -> None:
    (OUT / f"{pid}.md").write_text(f"## Sample run (real)\n\n{body}\n", encoding="utf-8")
    print("wrote", OUT / f"{pid}.md")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t01 = load("T01")
    scan = t01["api"]["scan"]
    prompt = t01["test"]["system_prompt"]
    analysis = scan["/api/analyze"]["response"]
    attacks = scan["/api/attacks"]["response"]["attacks"]
    results = scan["/api/run"]["response"]
    source = "Source: test T01 (`test-data/outputs/T01.json`), Gemini 3.5 Flash-Lite."

    short = dict(analysis, rules=shorten_list(analysis["rules"], 3, "rules"),
                 weak_spots=shorten_list(analysis["weak_spots"], 2, "weak spots"))
    write("P1", f"{source}\n\n**Input** `{{system_prompt}}`: the built-in Copperleaf Travel example bot\n\n"
                f"{block(prompt.strip())}\n\n**Actual output** (shortened where marked; the full output is in "
                f"`test-data/outputs/T01.json`)\n\n{block(js(short), 'json')}")

    shown = attacks[:2]
    write("P2", f"{source}\n\n**Input:** `{{per_category}}` = 2, `{{total}}` = 8, `{{system_prompt}}` = the Copperleaf "
                f"prompt (P1's sample), `{{analysis_json}}` = P1's output above.\n\n"
                f"**Actual output** ({len(attacks)} attacks; the first 2 are shown, after code added the IDs)\n\n"
                f"{block(js({'attacks': shown}), 'json')}")

    # Use the first failed attack, so P3 and P4 show the same, interesting case.
    case = next((r for r in results if r["judgment"] and r["judgment"]["verdict"] == "Fail"), results[0])
    attack = case["attack"]
    write("P3", f"{source}\n\n**Input:** `{{system_prompt}}` = the Copperleaf prompt; `{{attack_prompt}}` = attack "
                f"{attack['id']} ({attack['technique']}):\n\n{block(attack['prompt'])}\n\n"
                f"**Actual output** (labelled as a prediction in the app)\n\n"
                f"{block(js({'predicted_reply': case['reply']['text']}), 'json')}")

    write("P4", f"{source}\n\n**Input:** attack {attack['id']} (above, in P3's sample) and P3's predicted reply:\n\n"
                f"{block(case['reply']['text'])}\n\n**Actual output**\n\n{block(js(case['judgment']), 'json')}\n\n"
                f"Code check: evidence quote found in the reply = **{case['evidence_verified']}**.")

    t07_path = OUTPUTS / "T07.json"
    harden = json.loads(t07_path.read_text(encoding="utf-8"))["api"].get("/api/harden", {})
    if harden.get("status") == 200:
        h = harden["response"]["hardening"]
        short_h = dict(h, fixes=shorten_list(h["fixes"], 2, "fixes"),
                       hardened_prompt=shorten_text(h["hardened_prompt"], 8))
        failed = [r for r in json.loads(t07_path.read_text(encoding="utf-8"))["api"]["scan"]["/api/run"]["response"]
                  if r["judgment"] and r["judgment"]["verdict"] == "Fail"]
        lines = "\n".join(f"- {r['attack']['id']} [{r['judgment']['severity']}] {r['attack']['technique']}: "
                          f"{r['judgment']['reason']}" for r in failed)
        write("P5", f"Source: test T07 (`test-data/outputs/T07.json`), Gemini 3.5 Flash-Lite.\n\n"
                    f"**Input:** `{{system_prompt}}` = the Copperleaf prompt; `{{weak_spots}}` = P1's weak spots; "
                    f"`{{failed_attacks}}` =\n\n{block(lines or '(none)')}\n\n**Actual output** (shortened where "
                    f"marked; the full output is in `test-data/outputs/T07.json`)\n\n"
                    f"{block(js(short_h), 'json')}")
    else:
        print("P5 skipped: T07 has no successful harden step yet")


if __name__ == "__main__":
    main()
