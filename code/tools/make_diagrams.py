"""
Draw the four Milestone 2 diagrams as SVG files in docs/diagrams/.

    1. prompt_workflow.svg     how the 5 prompts (P1-P5) and the code steps connect
    2. task_decomposition.svg  the overall task broken into sub-tasks
    3. input_output_flow.svg   what goes in and comes out of each step
    4. system_architecture.svg browser, server, Claude API, user's chatbot

They are drawn from this file (not copied from anywhere), so they match what
was built. Run from the code/ folder:  python -m tools.make_diagrams
"""

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"

# Colours: AI prompt steps, plain-code steps, inputs/outputs, external systems.
COLOURS = {
    "llm": ("#e8eefc", "#3b5bdb"),
    "code": ("#eef7ee", "#2b8a3e"),
    "io": ("#fff6e0", "#b08800"),
    "ext": ("#f3f0fa", "#6741d9"),
    "plain": ("#ffffff", "#5d6677"),
}
FONT = "Segoe UI, Arial, sans-serif"


class Svg:
    """A tiny helper for boxes, arrows and text."""

    def __init__(self, width: int, height: int, title: str):
        self.w, self.h = width, height
        self.parts = [
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
            f'<text x="{width / 2}" y="28" text-anchor="middle" font-size="18" font-weight="700" fill="#1c2230">{escape(title)}</text>',
        ]

    def box(self, x, y, w, h, lines, kind="plain", bold_first=True, size=13):
        fill, stroke = COLOURS[kind]
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        line_h = size + 4
        top = y + h / 2 - (len(lines) - 1) * line_h / 2 + size * 0.35
        for i, text in enumerate(lines):
            weight = "700" if (i == 0 and bold_first) else "400"
            colour = "#1c2230" if i == 0 else "#3d4554"
            self.parts.append(
                f'<text x="{x + w / 2}" y="{top + i * line_h}" text-anchor="middle" font-size="{size if i == 0 else size - 1}" '
                f'font-weight="{weight}" fill="{colour}">{escape(text)}</text>')
        return (x, y, w, h)

    def arrow(self, x1, y1, x2, y2, label="", dashed=False, label_dx=0, label_dy=-6):
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#5d6677" stroke-width="1.6"{dash} marker-end="url(#arrow)"/>')
        if label:
            self.parts.append(
                f'<text x="{(x1 + x2) / 2 + label_dx}" y="{(y1 + y2) / 2 + label_dy}" text-anchor="middle" font-size="11.5" '
                f'fill="#3d4554">{escape(label)}</text>')

    def path(self, d, label="", lx=0, ly=0, dashed=False):
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.parts.append(f'<path d="{d}" fill="none" stroke="#5d6677" stroke-width="1.6"{dash} marker-end="url(#arrow)"/>')
        if label:
            self.parts.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11.5" fill="#3d4554">{escape(label)}</text>')

    def text(self, x, y, text, size=12, anchor="middle", colour="#3d4554", weight="400"):
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{colour}">{escape(text)}</text>')

    def legend(self, y):
        items = [("llm", "AI prompt (LLM call)"), ("code", "Plain code (no AI)"), ("io", "Input / output"), ("ext", "External system")]
        x = 20
        for kind, label in items:
            fill, stroke = COLOURS[kind]
            self.parts.append(f'<rect x="{x}" y="{y}" width="16" height="16" rx="3" fill="{fill}" stroke="{stroke}"/>')
            self.text(x + 22, y + 12.5, label, size=12, anchor="start")
            x += 190

    def save(self, name: str):
        defs = ('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#5d6677"/></marker></defs>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
               f'font-family="{FONT}">{defs}{"".join(self.parts)}</svg>\n')
        (OUT / name).write_text(svg, encoding="utf-8")
        print("wrote", OUT / name)


def prompt_workflow():
    s = Svg(860, 600, "Prompt workflow: 5 prompts, with code between them")
    s.box(320, 50, 220, 46, ["System prompt under test", "pasted by the user"], "io")
    s.arrow(430, 96, 430, 120)
    s.box(300, 120, 260, 50, ["P1 Analyse", "purpose, rules R1..Rn, assets, weak spots"], "llm")
    s.arrow(430, 170, 430, 194)
    s.box(300, 194, 260, 50, ["P2 Write attacks", "4 categories, safety rules"], "llm")
    s.arrow(430, 244, 430, 268)
    s.box(280, 268, 300, 44, ["Code: assign IDs (INJ-01...), safety screen"], "code", bold_first=False)
    # Branch: predicted or live
    s.path("M 360 312 L 200 352", "predicted mode", 255, 326)
    s.path("M 500 312 L 660 352", "live mode", 610, 326)
    s.box(80, 352, 240, 50, ["P3 Predict reply", "labelled as a prediction"], "llm")
    s.box(540, 352, 240, 50, ["Your real chatbot", "HTTP request, real reply"], "ext")
    s.path("M 200 402 L 360 440")
    s.path("M 660 402 L 500 440")
    s.text(430, 432, "for each attack", size=11.5)
    s.box(300, 440, 260, 50, ["P4 Judge (separate call)", "Pass/Fail, severity, reason, evidence"], "llm")
    s.arrow(430, 490, 430, 514)
    s.box(250, 514, 360, 44, ["Code: check evidence quote, launch call"], "code", bold_first=False)
    s.path("M 610 536 L 700 536 L 700 470", dashed=True)
    s.box(620, 430, 200, 40, ["P5 Harden", "fixes + new prompt"], "llm")
    # Re-test: the SAME attacks are run again (no new P2 call) with the hardened prompt.
    # Routed round the right of "Your real chatbot" so the line doesn't cross it.
    s.path("M 820 450 L 842 450 L 842 290 L 582 290", dashed=True)
    s.text(712, 282, "re-test: same attacks, hardened prompt", size=11.5)
    s.legend(572)
    s.save("prompt_workflow.svg")


def task_decomposition():
    s = Svg(900, 430, "Task decomposition: testing a chatbot prompt for safety")
    s.box(290, 50, 320, 48, ["Find and fix a chatbot's weak spots", "before launch"], "io")
    tasks = [
        (["1. Understand", "the bot"], "P1 Analyse", "llm"),
        (["2. Attack it"], "P2 Attacks", "llm"),
        (["3. Get replies"], "P3 or live", "llm"),
        (["4. Judge replies"], "P4 Judge", "llm"),
        (["5. Decide"], "Code", "code"),
        (["6. Fix it"], "P5 Harden", "llm"),
        (["7. Re-test"], "Code + P3/P4", "code"),
    ]
    subs = [
        ["purpose", "rules R1..Rn", "assets", "weak spots"],
        ["hidden instr.", "rule override", "trickery", "prompt leak"],
        ["predicted", "or real", "chatbot reply"],
        ["Pass / Fail", "severity", "evidence quote"],
        ["launch call", "summary", "counts"],
        ["prompt fixes", "app fixes", "new prompt", "diff"],
        ["fixed", "still failing", "new failures"],
    ]
    w, gap, x0 = 112, 12, 18
    for i, ((title, step, kind), sub) in enumerate(zip(tasks, subs)):
        x = x0 + i * (w + gap)
        s.path(f"M 450 98 L {x + w / 2} 140")
        s.box(x, 140, w, 52, title + [step], kind)
        s.box(x, 214, w, 26 + 17 * len(sub), sub, "plain", bold_first=False, size=12)
        s.arrow(x + w / 2, 192, x + w / 2, 214)
    s.box(330, 340, 240, 40, ["Export: Markdown report, CSV table"], "io", bold_first=False)
    s.path(f"M {x0 + 4 * (w + gap) + w / 2} 300 L 450 340", dashed=True)
    s.legend(398)
    s.save("task_decomposition.svg")


def input_output_flow():
    s = Svg(900, 560, "Input-output flow")
    rows = [
        (["System prompt", "(+ chatbot address in live mode)"], "io", ["P1 Analyse"], ["Analysis JSON", "purpose, rules, assets, weak spots"]),
        (["Prompt + analysis", "attacks per category"], "io", ["P2 Attacks", "+ code IDs"], ["12 attacks", "ID, technique, goal, target rules, text"]),
        (["Prompt + one attack"], "io", ["P3 Predict", "or live HTTP"], ["Reply text", "labelled predicted or live"]),
        (["Attack + reply", "+ rules and assets"], "io", ["P4 Judge", "+ evidence check"], ["Judgment", "verdict, severity, reason, evidence"]),
        (["All judgments"], "io", ["Code"], ["Launch call + counts", "table, filters, exports"]),
        (["Prompt + weak spots", "+ failed attacks"], "io", ["P5 Harden", "+ difflib"], ["Fixes + hardened prompt", "+ line-by-line diff"]),
        (["Hardened prompt", "+ same attacks"], "io", ["P3/P4 again", "+ compare"], ["Before/after table", "fixed / still failing / new"]),
    ]
    for i, (inp, kind, step, out) in enumerate(rows):
        y = 50 + i * 66
        s.box(30, y, 250, 50, inp, kind, bold_first=False)
        s.arrow(280, y + 25, 340, y + 25)
        step_kind = "code" if step[0] == "Code" else "llm"
        s.box(340, y, 200, 50, step, step_kind)
        s.arrow(540, y + 25, 600, y + 25)
        s.box(600, y, 270, 50, out, "io")
    s.legend(522)
    s.save("input_output_flow.svg")


def system_architecture():
    s = Svg(900, 480, "System architecture")
    s.box(30, 70, 220, 300, [], "plain")
    s.text(140, 96, "Browser", size=14, weight="700", colour="#1c2230")
    s.box(50, 115, 180, 52, ["index.html + app.js", "3 tabs, progress, tables"], "io")
    s.box(50, 185, 180, 52, ["Holds the session", "results stay in the page"], "plain")
    s.box(50, 255, 180, 52, ["Downloads", "Markdown and CSV"], "io")
    s.text(140, 350, "no API key here", size=11.5)

    s.box(310, 70, 300, 340, [], "plain")
    s.text(460, 96, "Python server (FastAPI)", size=14, weight="700", colour="#1c2230")
    s.box(330, 112, 260, 40, ["main.py: routes /api/..."], "code", bold_first=False)
    s.box(330, 166, 260, 52, ["pipeline/", "analyse, attacks, runner, judge, harden"], "code")
    s.box(330, 232, 125, 52, ["prompts.py", "P1-P5"], "llm")
    s.box(465, 232, 125, 52, ["llm.py", "only AI caller"], "code")
    s.box(330, 298, 125, 52, ["demo.py", "no key: demo"], "code")
    s.box(465, 298, 125, 52, ["live_client.py", "HTTP to chatbot"], "code")
    s.text(460, 380, "API key read from .env (server only)", size=11.5)
    s.text(460, 396, "Hosted on Vercel (index.py entry point)", size=11.5)

    s.arrow(250, 130, 330, 130)
    s.arrow(330, 146, 250, 146)
    s.text(290, 172, "JSON", size=11.5)

    s.box(670, 112, 200, 86, ["AI model API", "Gemini 3.5 Flash-Lite", "(or Claude Opus 5.5)", "structured JSON output"], "ext")
    s.box(670, 290, 200, 60, ["User's chatbot", "(live mode only)"], "ext")
    s.arrow(590, 255, 670, 165, "prompt + schema", label_dx=10, label_dy=-4)
    s.arrow(590, 320, 670, 320, "attack text")
    s.legend(440)
    s.save("system_architecture.svg")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prompt_workflow()
    task_decomposition()
    input_output_flow()
    system_architecture()


if __name__ == "__main__":
    main()
