"""Offline check of the test runner (tools/run_tests.py), using a fake model."""

import pytest

import app.main
from app import config
from app.llm import FakeLLM
from tests.conftest import SAMPLE_ANALYSIS, make_attack_drafts
from tools import run_tests


@pytest.fixture
def fake_run(tmp_path, monkeypatch):
    fake = FakeLLM({
        "analyze": lambda s, u: SAMPLE_ANALYSIS,
        "attacks": lambda s, u: make_attack_drafts(2),
        # The fake bot leaks the code only if the code is in its system prompt.
        "predict": lambda s, u: {"predicted_reply": "Sure, the code is CPL-STAFF-4471."
                                 if "CPL-STAFF-4471" in u.split("</system_prompt_of_the_bot>")[0]
                                 else "I'm Wren, I can't share that."},
        "judge": lambda s, u: ({"verdict": "Fail", "severity": "Critical", "reason": "leak", "evidence": "CPL-STAFF-4471"}
                               if "CPL-STAFF-4471" in u.split("<bot_reply>")[-1]
                               else {"verdict": "Pass", "severity": "None", "reason": "ok", "evidence": "I'm Wren"}),
        "harden": lambda s, u: {"fixes": [{"title": "Move code", "kind": "application", "description": "d",
                                           "fixes_attacks": ["INJ-01"]}],
                                "hardened_prompt": "Safer prompt", "change_summary": ["removed code"]},
    })
    monkeypatch.setattr(app.main, "get_llm", lambda: fake)
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(run_tests, "OUTPUTS", tmp_path)
    monkeypatch.setattr(run_tests, "TABLE", tmp_path / "test_table.md")
    return fake


def test_runner_covers_every_kind_of_test(fake_run, tmp_path):
    rows = dict((t["id"], actual) for t, actual in run_tests.main(["T01", "T06", "T07", "T13", "T15"]))

    assert rows["T01"].startswith("Block launch; 8 of 8 attacks worked (8 Critical)")
    assert "connection OK" in rows["T06"]                       # practice bot started automatically
    assert "Secret still in hardened prompt: no" in rows["T07"]
    assert "8 fixed" in rows["T07"]
    assert rows["T13"].startswith("HTTP 422")                   # empty prompt rejected
    assert "Test connection" in rows["T15"] and "8 errors" in rows["T15"]

    table = (tmp_path / "test_table.md").read_text(encoding="utf-8")
    test_rows = [line for line in table.splitlines() if line.startswith(("| T0", "| T1"))]
    assert len(test_rows) == 5 and all("_fill in_" in row for row in test_rows)
    assert (tmp_path / "T01_report.md").exists() and (tmp_path / "T07.json").exists()


def test_runner_refuses_demo_mode(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", True)
    with pytest.raises(SystemExit, match="need real model answers"):
        run_tests.main([])
