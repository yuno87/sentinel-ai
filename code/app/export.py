"""
Step 8: export the report as Markdown and the evaluation table as CSV.

Both functions take plain data (the same data the browser shows), so the
export always matches what the user saw.
"""

import csv
import io
from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.pipeline.verdict import launch_call, summary_counts
from app.schemas import CATEGORY_LABEL, Analysis, AttackResult, ComparisonRow, Hardening

PREDICTED_NOTE = (
    "Replies in this report are PREDICTIONS made by an LLM of how a typical chatbot with this "
    "system prompt would respond. They are not real results from your chatbot."
)


class Report(BaseModel):
    """Everything needed to build a report. Sent by the browser."""
    system_prompt: str
    analysis: Analysis
    results: list[AttackResult]
    hardening: Optional[Hardening] = None
    retest_results: Optional[list[AttackResult]] = None
    comparison: Optional[list[ComparisonRow]] = None
    demo: bool = False


def _verdict_text(r: AttackResult) -> tuple[str, str]:
    if r.judgment is None:
        return "Error", "-"
    return r.judgment.verdict, r.judgment.severity


def _cell(text: str) -> str:
    """Make text safe for a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def to_markdown(report: Report) -> str:
    results = report.results
    counts = summary_counts(results)
    mode = results[0].reply.mode if results else "predicted"
    out: list[str] = []
    add = out.append

    add("# Sentinel AI security report")
    add(f"_Generated {date.today().isoformat()}. Mode: **{mode}**._\n")
    if report.demo:
        add("> **Demo data.** This report was produced in demo mode with pre-written responses.\n")
    if mode == "predicted":
        add(f"> **Note:** {PREDICTED_NOTE}\n")

    add(f"## Launch call: {launch_call(results)}\n")
    add(f"- Attacks run: {counts['total']} (pass {counts['pass']}, fail {counts['fail']}, error {counts['error']})")
    add(f"- Failures by severity: Critical {counts['Critical']}, High {counts['High']}, "
        f"Medium {counts['Medium']}, Low {counts['Low']}\n")

    a = report.analysis
    add("## What the bot is for\n")
    add(a.purpose + "\n")
    add("**Rules**\n")
    for rule in a.rules:
        add(f"- {rule.id}: {rule.text}")
    add("\n**Protected assets**\n")
    for asset in a.protected_assets:
        add(f"- {asset.name} ({asset.kind}): {asset.description}")
    add("\n**Weak spots in the prompt**\n")
    for w in a.weak_spots:
        quote = f' ("{w.quote}")' if w.quote else ""
        add(f"- **{w.issue}**{quote}: {w.why_it_matters}")

    add("\n## Evaluation\n")
    add("| ID | Category | Technique | Verdict | Severity | Reason |")
    add("|---|---|---|---|---|---|")
    for r in results:
        verdict, severity = _verdict_text(r)
        reason = r.judgment.reason if r.judgment else (r.reply.error or "")
        add(f"| {r.attack.id} | {CATEGORY_LABEL[r.attack.category]} | {_cell(r.attack.technique)} | "
            f"{verdict} | {severity} | {_cell(reason)} |")

    add("\n## Failure details\n")
    failed = [r for r in results if r.failed]
    if not failed:
        add("No failures.")
    for r in failed:
        label = "Predicted reply" if r.reply.mode == "predicted" else "Reply"
        add(f"### {r.attack.id}: {r.attack.technique} ({r.judgment.severity})")
        add(f"- **Goal:** {r.attack.goal}")
        add(f"- **Targets:** {', '.join(r.attack.target_rules) or '-'}")
        add(f"- **Reason:** {r.judgment.reason}")
        check = "" if r.evidence_verified else " _(quote not found in reply)_"
        add(f"- **Evidence:** \"{r.judgment.evidence}\"{check}\n")
        add("**Attack**\n")
        add("```text\n" + r.attack.prompt + "\n```\n")
        add(f"**{label}**\n")
        add("```text\n" + r.reply.text + "\n```\n")

    if report.hardening:
        h = report.hardening
        add("## Suggested fixes\n")
        for fix in h.fixes:
            kind = "Prompt change" if fix.kind == "prompt" else "Application change"
            fixes = ", ".join(fix.fixes_attacks) or "-"
            add(f"- **{fix.title}** [{kind}; fixes {fixes}]: {fix.description}")
        add("\n## Hardened system prompt\n")
        add("**What changed**\n")
        for line in h.change_summary:
            add(f"- {line}")
        add("\n```text\n" + h.hardened_prompt + "\n```\n")

    if report.comparison:
        add("## Re-test: before and after hardening\n")
        add("> The hardening step saw these attacks, so passing them is easier than passing new ones. "
            "Generate fresh attacks against the hardened prompt for a fair test.\n")
        add("| ID | Before | After | Result |")
        add("|---|---|---|---|")
        names = {"fixed": "Fixed", "still_failing": "Still failing",
                 "new_failure": "New failure", "still_passing": "Still passing"}
        for row in report.comparison:
            add(f"| {row.attack_id} | {row.before_verdict} ({row.before_severity}) | "
                f"{row.after_verdict} ({row.after_severity}) | {names[row.status]} |")

    add("\n## System prompt tested\n")
    add("```text\n" + report.system_prompt + "\n```")
    return "\n".join(out) + "\n"


CSV_COLUMNS = ["id", "category", "technique", "goal", "target_rules", "mode",
               "verdict", "severity", "reason", "evidence", "evidence_verified", "attack", "reply", "error"]


def to_csv(results: list[AttackResult]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for r in results:
        verdict, severity = _verdict_text(r)
        writer.writerow([
            r.attack.id, CATEGORY_LABEL[r.attack.category], r.attack.technique, r.attack.goal,
            " ".join(r.attack.target_rules), r.reply.mode, verdict, severity,
            r.judgment.reason if r.judgment else "", r.judgment.evidence if r.judgment else "",
            r.evidence_verified, r.attack.prompt, r.reply.text, r.reply.error or "",
        ])
    return buffer.getvalue()
