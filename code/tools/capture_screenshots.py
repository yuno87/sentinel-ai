"""
Take screenshots of REAL runs in the app, for the Milestone 2 PDF (Section 4)
and the repository screenshot (Section 5).

It starts the app on this computer (using the AI key in code/.env), opens it
in your installed Chrome via Playwright, clicks through a scan exactly like a
user would, and saves PNGs in docs/screenshots/:

    T01_report.png   the Report tab after scanning the built-in example (test T01's input)
    T01_detail.png   one failed attack opened, with the reply and the evidence quote
    T07_retest.png   Fix & re-test tab: before/after table (test T07's flow)
    repository.png   the GitHub repository page

Run from the code/ folder:  python -m tools.capture_screenshots
It refuses to run in demo mode: screenshots must show real model output.
"""

import socket
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

from app import config
from app.main import app

OUT = Path(__file__).resolve().parents[2] / "docs" / "screenshots"
REPO_URL = "https://github.com/yuno87/sentinel-ai"
LONG = 15 * 60 * 1000  # free AI keys are slow when rate limited: allow up to 15 minutes


def start_app() -> str:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.1)
    return f"http://127.0.0.1:{port}"


def main():
    if config.DEMO_MODE:
        raise SystemExit("Demo mode is on: screenshots must show real model output. Add a key to code/.env.")
    OUT.mkdir(parents=True, exist_ok=True)
    url = start_app()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1.5)

        # --- T01: scan the built-in example -------------------------------------
        page.goto(url)
        page.click("#btn-example")
        page.wait_for_function("document.getElementById('system-prompt').value.length > 0")
        page.click("summary:has-text('More options')")
        page.fill("#per-category", "2")
        page.click("#btn-scan")
        print("Scanning (real AI calls)...", flush=True)
        page.wait_for_selector("#tab-report:not([hidden])", timeout=LONG)
        page.screenshot(path=OUT / "T01_report.png", full_page=False)
        print("saved T01_report.png", flush=True)

        # Open the first failed attack (or the first row if none failed).
        page.click("#filter-verdict .chip[data-value='Fail']")
        rows = page.locator("tr.result-row")
        if rows.count() == 0:
            page.click("#filter-verdict .chip[data-value='']")
        page.locator("tr.result-row").first.click()
        # Screenshot the clicked row together with its opened detail.
        page.locator("tr.result-row").first.scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -80)")
        page.screenshot(path=OUT / "T01_detail.png")
        print("saved T01_detail.png", flush=True)

        # --- T07: fix and re-test ------------------------------------------------
        page.click(".tab[data-tab='fix']")
        page.click("#btn-harden")
        page.wait_for_selector("#retest-card:not([hidden])", timeout=LONG)
        page.click("#btn-retest")
        page.wait_for_selector("#retest .stat-row", timeout=LONG)
        page.locator("#retest-card").scroll_into_view_if_needed()
        page.locator("#retest-card").screenshot(path=OUT / "T07_retest.png")
        print("saved T07_retest.png", flush=True)

        # --- Repository page -----------------------------------------------------
        page.goto(REPO_URL)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=OUT / "repository.png", full_page=False)
        print("saved repository.png", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
