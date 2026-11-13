"""Tests for step 6 (hardening + diff) and step 7 (re-test comparison)."""

from app.llm import FakeLLM
from app.pipeline.harden import harden_prompt, prompt_diff, unfixed_failures
from app.pipeline.retest import compare, comparison_counts
from tests.test_run_and_judge import make_result


def results_for(attack, severities):
    return [make_result(attack.model_copy(update={"id": f"T-{i}"}), s) for i, s in enumerate(severities)]


def test_hardening_links_only_real_failures(analysis, attack):
    results = results_for(attack, ["Critical", "None"])  # T-0 failed, T-1 passed
    fake = FakeLLM({"harden": lambda s, u: {
        "fixes": [
            {"title": "Remove code from prompt", "kind": "application", "description": "d",
             "fixes_attacks": ["T-0", "T-1", "NOPE"]},
        ],
        "hardened_prompt": "New prompt",
        "change_summary": ["Removed the code"],
    }})
    h = harden_prompt(fake, "Old prompt", analysis, results)
    assert h.fixes[0].fixes_attacks == ["T-0"]
    assert h.fixes[0].title.startswith("FIX-1")
    assert unfixed_failures(h, results) == []
    # Only failures are listed for the model.
    assert "T-0" in fake.calls[0]["user"] and "T-1" not in fake.calls[0]["user"]


def test_prompt_diff():
    diff = prompt_diff("a\nb\nc", "a\nB\nc\nd")
    ops = [(d.op, d.text) for d in diff]
    assert ("same", "a") in ops
    assert ("remove", "b") in ops
    assert ("add", "B") in ops
    assert ("add", "d") in ops


def test_compare_buckets(attack):
    before = results_for(attack, ["High", "Low", "None", "None", None])
    after = results_for(attack, ["None", "Low", "Medium", "None", "None"])
    rows = compare(before, after)
    status = {r.attack_id: r.status for r in rows}
    assert status == {"T-0": "fixed", "T-1": "still_failing", "T-2": "new_failure", "T-3": "still_passing"}
    # T-4 errored before, so it is not compared.
    assert comparison_counts(rows) == {"fixed": 1, "still_failing": 1, "new_failure": 1, "still_passing": 1}
