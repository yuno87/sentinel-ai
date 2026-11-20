"""
Build the Milestone 2 PDF and the supporting document (technical report).

Each section is a Markdown file in docs/m2/. Placeholders pull in material
from the repository, so the PDF always matches the saved evidence:

    {{diagram:NAME}}              docs/diagrams/NAME.svg
    {{screenshot:NAME|Caption}}   docs/screenshots/NAME.png
    {{prompt_sheets}}             prompts/final/P*.md + docs/m2/sample_runs/P*.md
    {{module_table}}              docs/m2/module_status.md
    {{iteration_log}}             prompts/ITERATION_LOG.md + full text of v1 and v2
    {{test_table}}                test-data/test_table.md
    {{technical_report}}          docs/m2/06_technical_report.md
    {{batch}} {{prototype_link}} {{reel_link}} {{reel_seconds}}   docs/m2/links.json

Output (in docs/):
    M2_PE-B49-24_SentinelAI.pdf          the Milestone 2 PDF
    SentinelAI_TechnicalReport.pdf       the supporting document

Needs Chrome or Edge installed (used to print HTML to PDF).
Run from the code/ folder:  python -m tools.build_docs
"""

import base64
import json
import re
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
M2 = DOCS / "m2"
M2_PDF = DOCS / "M2_PE-B49-24_SentinelAI.pdf"
REPORT_PDF = DOCS / "SentinelAI_TechnicalReport.pdf"
BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1c2230; }
h1 { font-size: 18pt; margin: 0 0 10px; border-bottom: 2px solid #3b5bdb; padding-bottom: 4px; }
h1.section { page-break-before: always; }
h2 { font-size: 13.5pt; margin: 18px 0 6px; color: #23305f; }
h3 { font-size: 11.5pt; margin: 14px 0 4px; }
p, li { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #c9ced8; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #eef1f7; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f2f4f7; padding: 0 3px; border-radius: 3px; }
pre { background: #f6f7f9; border: 1px solid #e1e4ea; padding: 8px 10px; border-radius: 5px; white-space: pre-wrap;
      word-break: break-word; font-size: 8.3pt; line-height: 1.35; }
pre code { background: none; padding: 0; font-size: inherit; }
figure { margin: 10px 0 16px; text-align: center; page-break-inside: avoid; }
figure svg, figure img { max-width: 100%; height: auto; border: 1px solid #e1e4ea; }
figcaption { font-size: 9pt; color: #5d6677; margin-top: 4px; }
.cover { text-align: left; }
.cover h1 { font-size: 24pt; border: none; margin-top: 30px; }
.cover .course { color: #5d6677; font-size: 11pt; margin-top: 40px; }
.cover .subtitle { font-size: 13pt; color: #3d4554; margin-bottom: 24px; }
.sheet { page-break-before: always; }
.note { background: #fff8e1; border-left: 3px solid #b08800; padding: 6px 10px; font-size: 9.5pt; }
"""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def svg_figure(name: str) -> str:
    svg = read(DOCS / "diagrams" / f"{name}.svg")
    title = re.search(r">([^<]+)</text>", svg).group(1)  # the diagram's own title
    return f'<figure>{svg}<figcaption>Figure: {title}</figcaption></figure>'


def png_figure(name: str, caption: str) -> str:
    path = DOCS / "screenshots" / f"{name}.png"
    if not path.exists():
        return f'<p class="note">Missing screenshot: docs/screenshots/{name}.png</p>'
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<figure><img src="data:image/png;base64,{data}"><figcaption>{caption}</figcaption></figure>'


def demote(md: str, levels: int = 1) -> str:
    """Turn '# Title' into '## Title' (etc.) so included files fit under a section."""
    return re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1)) + levels) + " ", md, flags=re.M)


def prompt_sheets() -> str:
    parts = []
    for sheet in sorted((ROOT / "prompts" / "final").glob("P*.md")):
        pid = sheet.stem.split("_")[0]
        body = demote(read(sheet), 2)
        sample = M2 / "sample_runs" / f"{pid}.md"
        sample_md = demote(read(sample), 2) if sample.exists() else f"#### Sample run\n\nMissing: docs/m2/sample_runs/{pid}.md"
        parts.append(f'<div class="sheet">\n\n{body}\n\n{sample_md}\n\n</div>')
    return "### 2(c) Prompt sheets\n\nOne sheet per final prompt (5 prompts). Prompts are pasted as text. " \
           "Each sample run is a real run from the saved test outputs.\n\n" + "\n\n".join(parts)


def iteration_log() -> str:
    log = demote(read(ROOT / "prompts" / "ITERATION_LOG.md"), 2)
    log = re.sub(r"^### Prompt iteration log\n", "", log, flags=re.M)
    v1 = demote(read(ROOT / "prompts" / "v1" / "P0_baseline_single_prompt.md"), 3)
    v2a = demote(read(ROOT / "prompts" / "v2" / "P2v2_attacks.md"), 3)
    v2b = demote(read(ROOT / "prompts" / "v2" / "P3v2_predict_judge.md"), 3)
    v3 = demote(read(ROOT / "prompts" / "v3" / "P3v3_predict.md"), 3)
    log = re.sub(r"### Full text of each version.*", "", log, flags=re.S)
    return (log + "\n\n### Full text of each version\n\n" + v1 + "\n\n" + v2a + "\n\n" + v2b + "\n\n" + v3 +
            "\n\nv3's other four prompts (P1, P2, P4, P5) are identical to the final version.\n\n"
            "#### v4 (final)\n\nThe full text of v4 is the five final prompts, printed in full in the prompt "
            "sheets in Section 2(c) (P1 Analyse, P2 Attacks, P3 Predict, P4 Judge, P5 Harden).\n")


def test_table() -> str:
    table = read(ROOT / "test-data" / "test_table.md")
    return re.sub(r"^# Test table\n", "", table, flags=re.M)


def fill(md: str, links: dict) -> str:
    md = re.sub(r"\{\{diagram:(\w+)\}\}", lambda m: svg_figure(m.group(1)), md)
    md = re.sub(r"\{\{screenshot:(\w+)\|([^}]+)\}\}", lambda m: png_figure(m.group(1), m.group(2)), md)
    replacements = {
        "{{prompt_sheets}}": prompt_sheets,
        "{{module_table}}": lambda: read(M2 / "module_status.md"),
        "{{iteration_log}}": iteration_log,
        "{{test_table}}": test_table,
        "{{technical_report}}": lambda: demote(read(M2 / "06_technical_report.md"), 1),
    }
    for key, make in replacements.items():
        if key in md:
            md = md.replace(key, make())
    for key, value in links.items():
        md = md.replace("{{" + key + "}}", str(value))
    # Any other {{name}} is the text in docs/m2/parts/name.md.
    md = re.sub(r"\{\{(\w+)\}\}", lambda m: read(M2 / "parts" / f"{m.group(1)}.md").strip()
                if (M2 / "parts" / f"{m.group(1)}.md").exists() else m.group(0), md)
    return md


def to_html(md: str, title: str) -> str:
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "md_in_html"])
    # Each numbered section ("# 2. ...") starts on a new page, except the first.
    body = re.sub(r"<h1>(\d\. )", r'<h1 class="section">\1', body)
    return f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>'


def print_pdf(html_path: Path, pdf_path: Path) -> None:
    browser = next((b for b in BROWSERS if b.exists()), None)
    if browser is None:
        raise SystemExit("Chrome or Edge is needed to make the PDF.")
    subprocess.run([str(browser), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True, capture_output=True)
    print(f"wrote {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")


def main() -> None:
    links = json.loads(read(M2 / "links.json"))
    sections = sorted(p for p in M2.glob("0*.md") if not p.name.startswith("06_technical"))
    md = "\n\n".join(fill(read(p), links) for p in sections)
    html = DOCS / "M2_PE-B49-24_SentinelAI.html"
    html.write_text(to_html(md, "M2_PE-B49-24_SentinelAI"), encoding="utf-8")
    print_pdf(html, M2_PDF)

    report_md = fill(read(M2 / "06_technical_report.md"), links)
    report_html = DOCS / "SentinelAI_TechnicalReport.html"
    report_html.write_text(to_html(report_md, "SentinelAI_TechnicalReport"), encoding="utf-8")
    print_pdf(report_html, REPORT_PDF)


if __name__ == "__main__":
    main()
