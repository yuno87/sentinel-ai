"""
Extra numbers for the iteration log, read from a saved prompt experiment run.

The main summary measures format and coverage. This script looks at WHAT the
verdicts said, from the raw answers saved by tools/prompt_experiment.py:

    fail_pct        % of attacks judged Fail (an attack "worked")
    inconsistent    verdicts where Pass/Fail and severity disagree
                    (a Pass must have severity None; a Fail must not)
    rule_ids_pct    % of attacks whose target_rules are rule IDs like "R4"
                    (only possible when there is an analysis step)

Run from the code/ folder:
    python -m tools.experiment_verdicts                      # latest run
    python -m tools.experiment_verdicts 2026-11-20_2345      # a specific run
"""

import json
import re
import sys
from pathlib import Path

from tools.prompt_experiment import OUT_DIR, V1_LINE, parse_json_answer

RULE_ID = re.compile(r"^R\d+$")


def verdicts_for(version: str, raw) -> tuple[list[tuple[str, str]], list[list[str]]]:
    """Return ([(verdict, severity), ...], [target_rules per attack]) for one saved run."""
    pairs, rules = [], []
    if version == "v1":
        for line in raw.splitlines():
            m = V1_LINE.match(line)
            if m:
                pairs.append((m["verdict"].capitalize(), m["severity"].capitalize()))
    elif version == "v2":
        try:
            rules = [a["target_rules"] for a in parse_json_answer(raw["attacks"])["attacks"]]
        except (ValueError, KeyError):
            pass
        for answer in raw.get("verdicts", []):
            try:
                v = parse_json_answer(answer)
                pairs.append((v["verdict"], v["severity"]))
            except (ValueError, KeyError):
                pass
    else:  # v3 and v4 (the app's pipeline)
        for r in raw.get("results", []):
            rules.append(r["attack"]["target_rules"])
            if r["judgment"]:
                pairs.append((r["judgment"]["verdict"], r["judgment"]["severity"]))
    return pairs, rules


def main(argv: list[str]) -> dict:
    run_dir = OUT_DIR / argv[0] if argv else sorted(p for p in OUT_DIR.iterdir() if p.is_dir())[-1]
    stats = {}
    for version in ("v1", "v2", "v3", "v4"):
        pairs, rules = [], []
        for f in sorted(run_dir.glob(f"{version}_*.json")):
            p, r = verdicts_for(version, json.loads(f.read_text(encoding="utf-8"))["raw"])
            pairs += p
            rules += r
        if not pairs:
            continue
        fails = sum(1 for v, _ in pairs if v == "Fail")
        inconsistent = sum(1 for v, s in pairs if (v == "Pass") != (s == "None"))
        with_ids = sum(1 for r in rules if r and all(RULE_ID.match(x) for x in r))
        stats[version] = {
            "verdicts": len(pairs),
            "fail_pct": round(100 * fails / len(pairs)),
            "inconsistent": inconsistent,
            "rule_ids_pct": round(100 * with_ids / len(rules)) if rules else None,
        }
    lines = ["| Version | Verdicts | Judged Fail % | Pass/severity inconsistent | Target rules as IDs % |",
             "|---|---|---|---|---|"]
    for v, s in stats.items():
        lines.append(f"| {v} | {s['verdicts']} | {s['fail_pct']} | {s['inconsistent']} | "
                     f"{s['rule_ids_pct'] if s['rule_ids_pct'] is not None else 'n/a (no target rules)'} |")
    (run_dir / "verdicts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "verdicts.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved {run_dir / 'verdicts.md'}")
    return stats


if __name__ == "__main__":
    main(sys.argv[1:])
