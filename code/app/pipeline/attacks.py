"""
Step 3: generate attack prompts tailored to the bot.

Claude writes the attacks; our code then:
1. keeps the right number per category,
2. gives each one a predictable ID (INJ-01, OVR-01, JBK-01, LEAK-01, ...),
3. drops rule IDs that do not exist,
4. screens the text with a simple safety check, as a backup to the prompt rules.
"""

import re

from app import prompts
from app.llm import LLMClient, LLMError
from app.schemas import CATEGORY_PREFIX, Analysis, Attack, AttackDraftList

# Emails and web addresses. Anything not on example.com gets flagged.
EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
URL_RE = re.compile(r"https?://([\w.-]+)")

# A short list of clearly harmful topics we never want in a test. This is a
# backstop: the main protection is the instruction in prompts.SAFE_CONTENT_RULES.
HARMFUL_WORDS = ["bomb", "explosive", "weapon", "malware", "ransomware", "meth", "poison", "suicide"]


def safety_problems(text: str) -> list[str]:
    """Return a list of problems found in an attack's text (empty = OK)."""
    problems = []
    domains = EMAIL_RE.findall(text) + URL_RE.findall(text)
    for domain in domains:
        domain = domain.lower().rstrip(".")
        if domain != "example.com" and not domain.endswith(".example.com"):
            problems.append(f"uses a real-looking domain: {domain}")
    lowered = text.lower()
    for word in HARMFUL_WORDS:
        if re.search(rf"\b{word}", lowered):
            problems.append(f"mentions a harmful topic: {word}")
    return problems


def generate_attacks(
    llm: LLMClient, system_prompt: str, analysis: Analysis, per_category: int
) -> tuple[list[Attack], list[str]]:
    """
    Generate attacks. Returns (attacks, warnings).

    Warnings tell the user about anything we dropped, so nothing disappears silently.
    """
    drafts = llm.structured(
        task="attacks",
        system=prompts.ATTACKS_SYSTEM,
        user=prompts.attacks_user(system_prompt, analysis, per_category),
        output_model=AttackDraftList,
    ).attacks

    known_rules = {rule.id for rule in analysis.rules}
    warnings: list[str] = []
    attacks: list[Attack] = []

    # Go category by category so IDs are numbered within each category.
    for category, prefix in CATEGORY_PREFIX.items():
        in_category = [d for d in drafts if d.category == category]
        kept = 0
        for draft in in_category:
            if kept == per_category:
                break
            problems = safety_problems(f"{draft.goal}\n{draft.prompt}")
            if problems:
                warnings.append(f"Dropped a {category} attack ({draft.technique}): {'; '.join(problems)}")
                continue
            kept += 1
            attacks.append(
                Attack(
                    id=f"{prefix}-{kept:02d}",
                    category=draft.category,
                    technique=draft.technique,
                    goal=draft.goal,
                    target_rules=[r for r in draft.target_rules if r in known_rules],
                    prompt=draft.prompt,
                )
            )
        if kept < per_category:
            warnings.append(f"Only {kept} of {per_category} {category} attacks were usable.")

    if not attacks:
        raise LLMError("No usable attacks were generated. Try again.")
    return attacks, warnings
