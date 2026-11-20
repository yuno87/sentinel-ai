"""
Run the Milestone 2 test inputs (test-data/inputs/T01.json ...) through the
app and save everything it returns to test-data/outputs/.

Each test goes through the app's real web API, exactly like the page does
(analyse -> attacks -> run each attack -> summary), so the saved outputs are
what a user would see. Live-mode tests start the practice bot automatically.

Needs an API key in code/.env. It refuses to run in demo mode, because demo
answers are pre-written and must not be reported as test results.

Run from the code/ folder:

    python -m tools.run_tests              # all tests
    python -m tools.run_tests T01 T08      # only some tests

Afterwards, open test-data/test_table.md. The "Actual output" column is filled
in automatically; the tester compares it with "Expected" (and reads the saved
report for the details) and writes Pass or Fail by hand.
"""

import json
import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn
from fastapi.testclient import TestClient

from app import config
from app.main import app
from mock_bot.server import app as mock_bot_app

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "test-data" / "inputs"
OUTPUTS = ROOT / "test-data" / "outputs"
TABLE = ROOT / "test-data" / "test_table.md"


def start_practice_bot() -> str:
    """Start the practice chatbot on a free port, in the background. Returns its URL."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(mock_bot_app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.1)
    return f"http://127.0.0.1:{port}/chat"


class StepFailed(Exception):
    """An API step returned an error; the test records it as its actual output."""


def post(client: TestClient, path: str, body: dict, log: dict) -> dict:
    response = client.post(path, json=body)
    data = response.json() if "json" in response.headers.get("content-type", "") else response.text
    log[path] = {"status": response.status_code, "response": data}
    if response.status_code != 200:
        detail = data.get("detail") if isinstance(data, dict) else data
        if isinstance(detail, list):  # FastAPI validation errors
            detail = "; ".join(f"{'.'.join(map(str, d['loc'][1:]))}: {d['msg']}" for d in detail)
        raise StepFailed(f"HTTP {response.status_code} at {path}: {detail}")
    return data


def scan(client: TestClient, test: dict, prompt: str, log: dict, label: str = "") -> dict:
    """Analyse, write attacks, run them one by one, then summarise (like the page)."""
    steps = log.setdefault(f"scan{label}", {})
    analysis = post(client, "/api/analyze", {"system_prompt": prompt}, steps)
    attacks = post(client, "/api/attacks", {"system_prompt": prompt, "analysis": analysis,
                                           "per_category": test["per_category"]}, steps)["attacks"]
    results = []
    for attack in attacks:
        body = {"system_prompt": prompt, "analysis": analysis, "attacks": [attack],
                "mode": test["mode"], "live": test.get("live")}
        results.append(post(client, "/api/run", body, {})["results"][0])
    steps["/api/run"] = {"status": 200, "response": results}
    summary = post(client, "/api/summary", {"results": results}, steps)
    return {"analysis": analysis, "attacks": attacks, "results": results, "summary": summary}


def short_summary(s: dict) -> str:
    c = s["counts"]
    sev = ", ".join(f"{c[k]} {k}" for k in ("Critical", "High", "Medium", "Low") if c[k])
    text = f"{s['launch_call']}; {c['fail']} of {c['total']} attacks worked"
    if sev:
        text += f" ({sev})"
    if c["error"]:
        text += f"; {c['error']} errors"
    return text


def run_test(client: TestClient, test: dict) -> str:
    """Run one test, save its outputs, and return the short 'actual output' text."""
    log: dict = {}
    out_json = OUTPUTS / f"{test['id']}.json"
    try:
        if test["mode"] == "live":
            conn = post(client, "/api/live/test", {"live": test["live"]}, log)
            note = "connection OK" if conn["ok"] else f"Test connection: {conn['error']}"
        else:
            note = ""

        result = scan(client, test, test["system_prompt"], log)
        a = result["analysis"]
        actual = (f"{short_summary(result['summary'])}. Found {len(a['rules'])} rules, "
                  f"{len(a['protected_assets'])} protected assets, {len(a['weak_spots'])} weak spots")
        if note:
            actual = f"{note}. {actual}"

        report_body = {"system_prompt": test["system_prompt"], "analysis": a, "results": result["results"]}
        if test["kind"] == "harden_retest":
            hard = post(client, "/api/harden", report_body, log)
            hardened = hard["hardening"]["hardened_prompt"]
            after = [post(client, "/api/run", {"system_prompt": hardened, "analysis": a, "attacks": [atk],
                                               "mode": test["mode"], "live": test.get("live")}, {})["results"][0]
                     for atk in result["attacks"]]
            comp = post(client, "/api/compare", {"before": result["results"], "after": after}, log)
            cc = comp["comparison_counts"]
            kinds = [f["kind"] for f in hard["hardening"]["fixes"]]
            actual += (f". Fixes: {kinds.count('prompt')} prompt, {kinds.count('application')} app. "
                       f"Secret still in hardened prompt: {'yes' if 'CPL-STAFF-4471' in hardened else 'no'}. "
                       f"Re-test: {cc['fixed']} fixed, {cc['still_failing']} still failing, "
                       f"{cc['new_failure']} new failures ({comp['launch_call']})")
            report_body |= {"hardening": hard["hardening"], "retest_results": after, "comparison": comp["comparison"]}

        report = client.post("/api/export/markdown", json=report_body).text
        (OUTPUTS / f"{test['id']}_report.md").write_text(report, encoding="utf-8")
    except StepFailed as exc:
        actual = str(exc)

    out_json.write_text(json.dumps({"test": test, "actual_short": actual, "api": log},
                                   indent=2, ensure_ascii=False), encoding="utf-8")
    return actual


def write_table(rows: list[tuple[dict, str]]) -> None:
    # Pass/Fail is decided by a person and kept in test-data/pass_fail.json, so
    # re-running some tests never wipes the decisions for the others.
    decisions_file = ROOT / "test-data" / "pass_fail.json"
    decisions = json.loads(decisions_file.read_text(encoding="utf-8")) if decisions_file.exists() else {}
    lines = [
        "# Test table",
        "",
        "Generated by `code/tools/run_tests.py`. The Pass/Fail column is decided by hand after checking each "
        "actual output against the expected output (details in `outputs/Txx_report.md` and `outputs/Txx.json`) "
        "and kept in `pass_fail.json`.",
        "",
        "| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail |",
        "|---|---|---|---|---|---|",
    ]
    for test, actual in rows:
        clean = lambda s: s.replace("|", "\\|").replace("\n", " ")
        verdict = decisions.get(test["id"], "_fill in_")
        lines.append(f"| {test['id']} | {clean(test['title'])} ({test['mode']}, {test['chars']} chars) | {test['type']} | "
                     f"{clean(test['expected'])} | {clean(actual)} | {clean(verdict)} |")
    TABLE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> list[tuple[dict, str]]:
    if config.DEMO_MODE:
        raise SystemExit("The tests need real model answers, so they need ANTHROPIC_API_KEY in code/.env. "
                         "Without a key the app runs in demo mode, whose answers are pre-written and "
                         "can't be reported as test results.")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    wanted = set(argv)
    tests = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(INPUTS.glob("T*.json"))]
    tests = [t for t in tests if not wanted or t["id"] in wanted]

    bot_url = start_practice_bot() if any(t["mode"] == "live" for t in tests) else ""
    client = TestClient(app)
    rows = []
    for test in tests:
        if test.get("live"):
            test["live"]["url"] = test["live"]["url"].replace("{mock_bot_url}", bot_url)
        print(f"Running {test['id']} ({test['type']}): {test['title']} ...", flush=True)
        started = time.time()
        actual = run_test(client, test)
        print(f"  -> {actual}  [{time.time() - started:.0f}s]\n", flush=True)
        rows.append((test, actual))

    # Keep rows from earlier runs for tests that were not re-run this time.
    if wanted and TABLE.exists():
        previous = {json.loads((OUTPUTS / f"{p.stem}.json").read_text(encoding="utf-8"))["test"]["id"]:
                    json.loads((OUTPUTS / f"{p.stem}.json").read_text(encoding="utf-8"))
                    for p in INPUTS.glob("T*.json") if (OUTPUTS / f"{p.stem}.json").exists()}
        rows = [(prev["test"], prev["actual_short"]) for tid, prev in sorted(previous.items())]
    write_table(rows)
    print(f"Saved outputs in {OUTPUTS}\nTest table: {TABLE}")
    return rows


if __name__ == "__main__":
    main(sys.argv[1:])
