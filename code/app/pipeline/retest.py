"""
Step 7: compare results before and after hardening.

The same attacks are run against the hardened prompt, then each attack is
put in one bucket:
    fixed          failed before, passes now
    still_failing  failed before, still fails
    new_failure    passed before, fails now (the hardening broke something)
    still_passing  passed before and after

Note for the report: the hardening step saw these exact attacks, so passing
them is easier than passing new ones. That is why the app also offers "use the
hardened prompt as the new baseline" and generates fresh attacks.
"""

from app.schemas import AttackResult, ComparisonRow


def compare(before: list[AttackResult], after: list[AttackResult]) -> list[ComparisonRow]:
    after_by_id = {r.attack.id: r for r in after}
    rows = []
    for b in before:
        a = after_by_id.get(b.attack.id)
        # Skip attacks that errored in either run: we cannot compare them.
        if a is None or b.judgment is None or a.judgment is None:
            continue
        if b.failed and not a.failed:
            status = "fixed"
        elif b.failed and a.failed:
            status = "still_failing"
        elif not b.failed and a.failed:
            status = "new_failure"
        else:
            status = "still_passing"
        rows.append(ComparisonRow(
            attack_id=b.attack.id, status=status,
            before_verdict=b.judgment.verdict, before_severity=b.judgment.severity,
            after_verdict=a.judgment.verdict, after_severity=a.judgment.severity,
        ))
    return rows


def comparison_counts(rows: list[ComparisonRow]) -> dict:
    counts = {"fixed": 0, "still_failing": 0, "new_failure": 0, "still_passing": 0}
    for row in rows:
        counts[row.status] += 1
    return counts
