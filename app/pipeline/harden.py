"""
Step 6: suggest fixes and write a hardened system prompt.

Claude proposes fixes (each marked "prompt" or "application" and linked to
the attacks it fixes) and a rewritten prompt. Our code then:
- removes links to attack IDs that did not actually fail,
- numbers the fixes FIX-1, FIX-2, ...,
- builds a line-by-line diff so the user can see what changed.
"""

import difflib

from app import prompts
from app.llm import LLMClient, LLMError
from app.schemas import Analysis, AttackResult, DiffLine, Hardening


def harden_prompt(
    llm: LLMClient, system_prompt: str, analysis: Analysis, results: list[AttackResult]
) -> Hardening:
    hardening = llm.structured(
        task="harden",
        system=prompts.HARDEN_SYSTEM,
        user=prompts.harden_user(system_prompt, analysis, results),
        output_model=Hardening,
    )
    if not hardening.hardened_prompt.strip():
        raise LLMError("The hardened prompt came back empty. Try again.")

    failed_ids = {r.attack.id for r in results if r.failed}
    for number, fix in enumerate(hardening.fixes, start=1):
        fix.fixes_attacks = [a for a in fix.fixes_attacks if a in failed_ids]
        if not fix.title.startswith("FIX-"):
            fix.title = f"FIX-{number}: {fix.title}"
    return hardening


def prompt_diff(old: str, new: str) -> list[DiffLine]:
    """Line-by-line diff using Python's built-in difflib."""
    lines = []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        code, text = line[:2], line[2:]
        if code == "  ":
            lines.append(DiffLine(op="same", text=text))
        elif code == "+ ":
            lines.append(DiffLine(op="add", text=text))
        elif code == "- ":
            lines.append(DiffLine(op="remove", text=text))
        # "? " lines are difflib hints about characters; we skip them.
    return lines


def unfixed_failures(hardening: Hardening, results: list[AttackResult]) -> list[str]:
    """Failed attacks that no fix claims to address, so the UI can point them out."""
    covered = {a for fix in hardening.fixes for a in fix.fixes_attacks}
    return [r.attack.id for r in results if r.failed and r.attack.id not in covered]
