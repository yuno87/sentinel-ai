# 5. Repository

Repository: <https://github.com/yuno87/sentinel-ai> (public). It follows the required layout:
`README.md`, `prompts/` (`v1/`, `v2/`, `v3/`, `final/`), `code/`, `test-data/`, `docs/` and `CHANGELOG.md`.

{{screenshot:repository|The public GitHub repository}}

**What changed since Milestone 1** (dated entries in `CHANGELOG.md`, dated commits on GitHub):

- Built the full app: a 5-prompt pipeline (P1 Analyse to P5 Harden) with structured JSON output, a web page with Setup, Report and Fix & re-test tabs, live mode for real chatbots, and Markdown/CSV export.
- Saved every prompt version: the Milestone 1 prompt (`prompts/v1/`), the first split version (`prompts/v2/`) and the final prompts (`prompts/final/`, generated from the code so they always match).
- Added scripts that produce the evidence in this report: `tools/prompt_experiment.py` (iteration log numbers) and `tools/run_tests.py` (test table), with all inputs and raw outputs saved in `test-data/`.
- Added Gemini support so the prototype runs on a free API key, and an automatic demo mode when no key is set.
- 65 automated tests (offline, using a fake model) check every pipeline step.
