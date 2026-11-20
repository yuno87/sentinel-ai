"""
Step 5: judge each reply as Pass or Fail.

This is a SEPARATE Claude call from the one that produced the reply (in
predicted mode), with its own system prompt. The judge only sees the attack
and the reply, never the predictor's instructions.

After the judge answers, our code:
- makes verdict and severity consistent (a Pass is always severity None),
- checks that the evidence quote really appears in the reply.
"""

import re

from app import prompts
from app.llm import LLMClient
from app.schemas import Analysis, Attack, Judgment


def _normalise(text: str) -> str:
    """Lower-case, unify quote marks and squash whitespace, for fair matching."""
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \"'.")


def evidence_is_in_reply(evidence: str, reply_text: str) -> bool:
    """True if the judge's quote can be found in the reply."""
    quote = _normalise(evidence)
    return bool(quote) and quote in _normalise(reply_text)


def judge_reply(
    llm: LLMClient, system_prompt: str, analysis: Analysis, attack: Attack, reply_text: str
) -> tuple[Judgment, bool]:
    """Return (judgment, evidence_verified)."""
    judgment = llm.structured(
        task="judge",
        system=prompts.JUDGE_SYSTEM,
        user=prompts.judge_user(system_prompt, analysis, attack, reply_text),
        output_model=Judgment,
    )

    # Consistency rules, so the table and launch call can trust the data.
    if judgment.verdict == "Pass":
        judgment.severity = "None"
    elif judgment.severity == "None":
        # A Fail must have a severity; take the lowest rather than invent one.
        judgment.severity = "Low"

    return judgment, evidence_is_in_reply(judgment.evidence, reply_text)
