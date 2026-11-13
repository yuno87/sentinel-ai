"""
The web server: FastAPI routes for each step, plus the static web page.

The server is stateless: the browser keeps the current analysis, attacks and
results, and sends what each step needs. That keeps this file short (each
route just calls one pipeline function) and means there is no database.

The Claude API key is only used here, on the server. The browser never sees it.

Run:  uvicorn app.main:app --reload     then open http://127.0.0.1:8000
API docs are generated automatically at http://localhost:8000/docs
"""

from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.examples import EXAMPLE_NAME, EXAMPLE_SYSTEM_PROMPT
from app.export import Report, to_csv, to_markdown
from app.live_client import LiveClientError, send_attack
from app.llm import LLMError, get_llm
from app.pipeline.analyze import analyze_prompt
from app.pipeline.attacks import generate_attacks
from app.pipeline.harden import harden_prompt, prompt_diff, unfixed_failures
from app.pipeline.retest import compare, comparison_counts
from app.pipeline.runner import run_attacks
from app.pipeline.verdict import launch_call, summary_counts
from app.schemas import Analysis, Attack, AttackResult, LiveConfig, Mode

app = FastAPI(title="Sentinel AI", description="Prompt safety tester for chatbots")


@app.exception_handler(LLMError)
def llm_error_handler(_request: Request, exc: LLMError):
    """Show Claude/API problems to the user as a clear message, not a crash."""
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.middleware("http")
async def always_fresh_page_files(request: Request, call_next):
    """
    Tell the browser to check for a newer copy of the page files every time.

    Without this, a browser can keep an old app.js after the code changes, and
    the old page then calls routes that no longer match the server.
    """
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

SystemPrompt = Field(min_length=1, max_length=config.MAX_SYSTEM_PROMPT_CHARS)


class AnalyzeIn(BaseModel):
    system_prompt: str = SystemPrompt


class AttacksIn(BaseModel):
    system_prompt: str = SystemPrompt
    analysis: Analysis
    per_category: int = Field(default=config.DEFAULT_ATTACKS_PER_CATEGORY, ge=1, le=config.MAX_ATTACKS_PER_CATEGORY)


class RunIn(BaseModel):
    system_prompt: str = SystemPrompt
    analysis: Analysis
    attacks: list[Attack] = Field(min_length=1)
    mode: Mode = "predicted"
    live: Optional[LiveConfig] = None


class HardenIn(BaseModel):
    system_prompt: str = SystemPrompt
    analysis: Analysis
    results: list[AttackResult]


class RetestIn(RunIn):
    before: list[AttackResult]


class CsvIn(BaseModel):
    results: list[AttackResult]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/info")
def info():
    """Tells the page which mode the server is in (never the key itself)."""
    return {"demo": config.DEMO_MODE, "model": config.MODEL, "has_api_key": bool(config.ANTHROPIC_API_KEY),
            "default_per_category": config.DEFAULT_ATTACKS_PER_CATEGORY,
            "max_per_category": config.MAX_ATTACKS_PER_CATEGORY}


@app.get("/api/example")
def example():
    return {"name": EXAMPLE_NAME, "system_prompt": EXAMPLE_SYSTEM_PROMPT}


@app.post("/api/analyze")
def analyze(body: AnalyzeIn) -> Analysis:
    return analyze_prompt(get_llm(), body.system_prompt)


@app.post("/api/attacks")
def attacks(body: AttacksIn):
    attack_list, warnings = generate_attacks(get_llm(), body.system_prompt, body.analysis, body.per_category)
    return {"attacks": attack_list, "warnings": warnings}


def _run(body: RunIn) -> list[AttackResult]:
    if body.mode == "live" and body.live is None:
        raise LLMError("Live mode needs an endpoint. Fill in the live endpoint settings.")
    return run_attacks(get_llm(), body.mode, body.system_prompt, body.analysis, body.attacks, body.live)


@app.post("/api/run")
def run(body: RunIn):
    results = _run(body)
    return {"results": results, "launch_call": launch_call(results), "counts": summary_counts(results)}


@app.post("/api/harden")
def harden(body: HardenIn):
    hardening = harden_prompt(get_llm(), body.system_prompt, body.analysis, body.results)
    return {
        "hardening": hardening,
        "diff": prompt_diff(body.system_prompt, hardening.hardened_prompt),
        "unfixed": unfixed_failures(hardening, body.results),
    }


@app.post("/api/retest")
def retest(body: RetestIn):
    """Run the same attacks against the hardened prompt (sent as system_prompt)."""
    results = _run(body)
    rows = compare(body.before, results)
    return {"results": results, "launch_call": launch_call(results), "counts": summary_counts(results),
            "comparison": rows, "comparison_counts": comparison_counts(rows)}


class CompareIn(BaseModel):
    before: list[AttackResult]
    after: list[AttackResult]


class LiveTestIn(BaseModel):
    live: LiveConfig


@app.post("/api/summary")
def summary(body: CsvIn):
    """
    Launch call and counts for a list of results.

    The page runs attacks a few at a time (so it can show "7 of 12" progress),
    then asks for the summary here, so the launch-call rule stays in Python.
    """
    return {"launch_call": launch_call(body.results), "counts": summary_counts(body.results)}


@app.post("/api/compare")
def compare_results(body: CompareIn):
    """Before/after comparison for a re-test that the page ran attack by attack."""
    rows = compare(body.before, body.after)
    return {"launch_call": launch_call(body.after), "counts": summary_counts(body.after),
            "comparison": rows, "comparison_counts": comparison_counts(rows)}


@app.post("/api/live/test")
def test_live_connection(body: LiveTestIn):
    """Send one harmless message to the live endpoint so the user can check their settings."""
    try:
        reply = send_attack(body.live, "Hello! This is a connection test from Sentinel AI.")
        return {"ok": True, "reply": reply}
    except LiveClientError as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/api/export/markdown")
def export_markdown(report: Report):
    return Response(to_markdown(report), media_type="text/markdown",
                    headers={"Content-Disposition": 'attachment; filename="sentinel-report.md"'})


@app.post("/api/export/csv")
def export_csv(body: CsvIn):
    return Response(to_csv(body.results), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="sentinel-results.csv"'})


# ---------------------------------------------------------------------------
# The web page
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")
