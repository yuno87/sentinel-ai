"""Step 2: work out what the bot is for and where it is weak."""

from app import prompts
from app.llm import LLMClient
from app.schemas import Analysis


def analyze_prompt(llm: LLMClient, system_prompt: str) -> Analysis:
    """Ask Claude to analyse the system prompt and return a validated Analysis."""
    analysis = llm.structured(
        task="analyze",
        system=prompts.ANALYZE_SYSTEM,
        user=prompts.analyze_user(system_prompt),
        output_model=Analysis,
    )

    # Make rule IDs predictable (R1, R2, ...) even if the model numbered them
    # differently, because attacks and fixes refer to these IDs.
    for number, rule in enumerate(analysis.rules, start=1):
        rule.id = f"R{number}"
    return analysis
