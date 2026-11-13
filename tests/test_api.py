"""
End-to-end tests of the web API, using demo mode (no API key, no cost).

This walks the whole flow the browser uses: example -> analyze -> attacks ->
run -> harden -> retest -> export.
"""

import csv
import io

import pytest
from fastapi.testclient import TestClient

from app import config


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", True)
    from app.main import app
    return TestClient(app)


def test_full_flow_in_demo_mode(client):
    prompt = client.get("/api/example").json()["system_prompt"]

    analysis = client.post("/api/analyze", json={"system_prompt": prompt}).json()
    assert analysis["reads_untrusted_content"] is True

    body = client.post("/api/attacks", json={"system_prompt": prompt, "analysis": analysis, "per_category": 3}).json()
    attacks = body["attacks"]
    assert len(attacks) == 12 and attacks[0]["id"] == "INJ-01"

    run = client.post("/api/run", json={"system_prompt": prompt, "analysis": analysis,
                                        "attacks": attacks, "mode": "predicted"}).json()
    assert run["launch_call"] == "Block launch"
    assert all(r["reply"]["mode"] == "predicted" for r in run["results"])
    assert all(r["evidence_verified"] for r in run["results"]), "every canned quote should be found"

    hard = client.post("/api/harden", json={"system_prompt": prompt, "analysis": analysis,
                                            "results": run["results"]}).json()
    assert any(d["op"] == "add" for d in hard["diff"])
    assert hard["unfixed"] == []
    kinds = {f["kind"] for f in hard["hardening"]["fixes"]}
    assert kinds == {"prompt", "application"}

    re = client.post("/api/retest", json={"system_prompt": hard["hardening"]["hardened_prompt"],
                                          "analysis": analysis, "attacks": attacks,
                                          "mode": "predicted", "before": run["results"]}).json()
    counts = re["comparison_counts"]
    assert counts["fixed"] == 8 and counts["still_failing"] == 1 and counts["new_failure"] == 1
    assert re["launch_call"] == "Fix before launch"

    report = {"system_prompt": prompt, "analysis": analysis, "results": run["results"],
              "hardening": hard["hardening"], "retest_results": re["results"],
              "comparison": re["comparison"], "demo": True}
    md = client.post("/api/export/markdown", json=report).text
    assert "# Sentinel AI security report" in md
    assert "PREDICTIONS" in md and "Demo data" in md
    assert "Launch call: Block launch" in md

    csv_text = client.post("/api/export/csv", json={"results": run["results"]}).text
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == 12 and rows[0]["id"] == "INJ-01" and rows[0]["mode"] == "predicted"


def test_attack_by_attack_flow_used_by_the_page(client):
    """The page runs one attack per request (for progress), then asks for the summary and comparison."""
    prompt = client.get("/api/example").json()["system_prompt"]
    analysis = client.post("/api/analyze", json={"system_prompt": prompt}).json()
    attacks = client.post("/api/attacks", json={"system_prompt": prompt, "analysis": analysis}).json()["attacks"]

    def run_each(system_prompt):
        return [client.post("/api/run", json={"system_prompt": system_prompt, "analysis": analysis,
                                              "attacks": [a]}).json()["results"][0] for a in attacks]

    before = run_each(prompt)
    summary = client.post("/api/summary", json={"results": before}).json()
    assert summary["launch_call"] == "Block launch" and summary["counts"]["fail"] == 9

    hardened = client.post("/api/harden", json={"system_prompt": prompt, "analysis": analysis,
                                                "results": before}).json()["hardening"]["hardened_prompt"]
    after = run_each(hardened)
    comp = client.post("/api/compare", json={"before": before, "after": after}).json()
    assert comp["comparison_counts"] == {"fixed": 8, "still_failing": 1, "new_failure": 1, "still_passing": 2}
    assert comp["launch_call"] == "Fix before launch"


def test_live_connection_check_reports_errors(client):
    r = client.post("/api/live/test", json={"live": {"url": "http://127.0.0.1:1/chat"}}).json()
    assert r["ok"] is False and r["error"]
    r = client.post("/api/live/test", json={"live": {"url": "ftp://bot.example.com"}}).json()
    assert r["ok"] is False and "http" in r["error"]


def test_demo_mode_rejects_other_prompts(client):
    r = client.post("/api/analyze", json={"system_prompt": "You are a pirate bot."})
    assert r.status_code == 502
    assert "Demo mode" in r.json()["detail"]


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", False)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    from app.main import app
    r = TestClient(app).post("/api/analyze", json={"system_prompt": "x"})
    assert r.status_code == 502
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_info_never_exposes_the_key(monkeypatch, client):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-secret-test")
    text = client.get("/api/info").text
    assert "sk-ant" not in text


def test_empty_prompt_rejected(client):
    assert client.post("/api/analyze", json={"system_prompt": ""}).status_code == 422
