"""
Data models for Sentinel AI, written with Pydantic.

Two kinds of models live here:

1. **LLM output models**: the exact JSON shape we ask Claude to return. We turn
   each one into a JSON Schema and send it with the request (structured
   output), then validate Claude's reply against the same class. If the reply
   does not match, Pydantic raises an error and we never use bad data.

2. **App models**: what the rest of the app passes around (attacks with IDs,
   results, reports). Some fields, like attack IDs, are filled in by our own
   code instead of the model, so they are always in the right format.

Rule for LLM output models: keep them simple (strings, lists, enums), because
structured output supports a subset of JSON Schema. Extra checks, such as
"a Pass must have severity None", are done in Python after parsing.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared vocabulary
# ---------------------------------------------------------------------------

Category = Literal[
    "prompt_injection",
    "instruction_override",
    "jailbreak",
    "system_prompt_leak",
]

# Every category gets a short prefix for attack IDs, e.g. INJ-01.
CATEGORY_PREFIX: dict[str, str] = {
    "prompt_injection": "INJ",
    "instruction_override": "OVR",
    "jailbreak": "JBK",
    "system_prompt_leak": "LEAK",
}

# Human-friendly names for the UI and reports.
CATEGORY_LABEL: dict[str, str] = {
    "prompt_injection": "Prompt injection",
    "instruction_override": "Instruction override",
    "jailbreak": "Jailbreak",
    "system_prompt_leak": "System prompt leak",
}

Verdict = Literal["Pass", "Fail"]
Severity = Literal["Critical", "High", "Medium", "Low", "None"]

# Higher number = worse. Used for sorting and for the launch call.
SEVERITY_RANK: dict[str, int] = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}

Mode = Literal["predicted", "live"]


# ---------------------------------------------------------------------------
# Step 2: analysis of the system prompt (LLM output)
# ---------------------------------------------------------------------------

class Rule(BaseModel):
    id: str = Field(description="Short ID like R1, R2, ...")
    text: str = Field(description="The rule in plain words")


class ProtectedAsset(BaseModel):
    name: str
    kind: Literal["secret", "user_data", "system_prompt", "other"]
    description: str


class WeakSpot(BaseModel):
    issue: str = Field(description="What is weak about how the prompt is written")
    why_it_matters: str
    quote: str = Field(description="The exact words from the prompt, or empty if it is something missing")


class Analysis(BaseModel):
    purpose: str
    rules: list[Rule]
    protected_assets: list[ProtectedAsset]
    capabilities: list[str] = Field(description="Tools, data access, reading pasted content, etc.")
    reads_untrusted_content: bool = Field(description="Does the bot read emails, documents, web pages or other text it did not write?")
    weak_spots: list[WeakSpot]


# ---------------------------------------------------------------------------
# Step 3: attacks
# ---------------------------------------------------------------------------

class AttackDraft(BaseModel):
    """One attack as Claude writes it. Our code adds the ID afterwards."""
    category: Category
    technique: str = Field(description="Short technique name, e.g. 'Fake admin claim'")
    goal: str = Field(description="What the attacker is trying to make the bot do")
    target_rules: list[str] = Field(description="Rule IDs from the analysis, e.g. ['R2']")
    prompt: str = Field(description="The full message the attacker sends to the bot")


class AttackDraftList(BaseModel):
    attacks: list[AttackDraft]


class Attack(AttackDraft):
    """An attack with its ID (e.g. INJ-01), assigned by our code."""
    id: str


# ---------------------------------------------------------------------------
# Step 4: replies
# ---------------------------------------------------------------------------

class PredictedReply(BaseModel):
    """LLM output for predicted mode."""
    predicted_reply: str


class Reply(BaseModel):
    attack_id: str
    mode: Mode
    text: str
    # Set if the live endpoint failed (timeout, bad status, etc.).
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Step 5: judging
# ---------------------------------------------------------------------------

class Judgment(BaseModel):
    """LLM output from the judge."""
    verdict: Verdict
    severity: Severity
    reason: str = Field(description="One line explaining the verdict")
    evidence: str = Field(description="A short exact quote from the reply that supports the verdict")


class AttackResult(BaseModel):
    """Everything about one attack after it has been run and judged."""
    attack: Attack
    reply: Reply
    # None when the attack could not be run (e.g. the live endpoint failed).
    # We never guess a verdict for an attack that did not run.
    judgment: Optional[Judgment] = None
    # True if the evidence quote really appears in the reply. The judge is an
    # LLM too, so we check its quote instead of trusting it.
    evidence_verified: bool = False

    @property
    def failed(self) -> bool:
        return self.judgment is not None and self.judgment.verdict == "Fail"


# ---------------------------------------------------------------------------
# Step 6: launch call, fixes and hardened prompt
# ---------------------------------------------------------------------------

LaunchCall = Literal["Block launch", "Hold launch", "Fix before launch", "No failures found"]


class Fix(BaseModel):
    title: str
    kind: Literal["prompt", "application"] = Field(
        description="'prompt' = change the system prompt; 'application' = change the app code around the bot"
    )
    description: str
    fixes_attacks: list[str] = Field(description="Attack IDs this fix addresses, e.g. ['INJ-01']")


class Hardening(BaseModel):
    """LLM output from the hardening step."""
    fixes: list[Fix]
    hardened_prompt: str
    change_summary: list[str] = Field(description="Short bullet points describing what changed")


class DiffLine(BaseModel):
    op: Literal["same", "add", "remove"]
    text: str


# ---------------------------------------------------------------------------
# Step 7: re-test comparison
# ---------------------------------------------------------------------------

ComparisonStatus = Literal["fixed", "still_failing", "new_failure", "still_passing"]


class ComparisonRow(BaseModel):
    attack_id: str
    status: ComparisonStatus
    before_verdict: Verdict
    before_severity: Severity
    after_verdict: Verdict
    after_severity: Severity


# ---------------------------------------------------------------------------
# Live mode configuration (sent by the browser)
# ---------------------------------------------------------------------------

class LiveConfig(BaseModel):
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    # JSON with the placeholder {{attack}}, e.g. {"message": "{{attack}}"}
    body_template: str = '{"message": "{{attack}}"}'
    # Where the reply is in the response JSON, e.g. "reply" or "choices.0.message.content"
    reply_path: str = "reply"
