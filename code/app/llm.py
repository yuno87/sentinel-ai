"""
One small wrapper around the Claude API.

Every pipeline step calls `llm.structured(...)`: it sends a system prompt and a
user message, asks for JSON matching a Pydantic class, and returns a
validated object of that class.

Why a wrapper?
- All API details (model, effort, fallbacks, error handling) live in one place.
- Tests can swap in a fake client with the same `structured` method, so they
  run offline and free.
- Demo mode swaps in a client that plays back canned responses.
"""

from __future__ import annotations

import copy
import json
from typing import Protocol, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app import config

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when Claude cannot give us a usable answer."""


class LLMClient(Protocol):
    """Anything with this method can be used as the LLM (real, fake or demo)."""

    def structured(self, task: str, system: str, user: str, output_model: type[T]) -> T: ...


# ---------------------------------------------------------------------------
# Turning a Pydantic class into a schema Claude can follow
# ---------------------------------------------------------------------------

def to_strict_schema(model: type[BaseModel]) -> dict:
    """
    Convert a Pydantic model into the JSON Schema format used by structured output.

    Structured output needs every object to list all its properties as
    `required` and to set `additionalProperties: false`. Pydantic does not do
    that by default, so we walk the schema and add them. We also inline `$ref`
    references so the schema is one simple nested object.
    """
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            # Replace {"$ref": "#/$defs/Name"} with the definition itself.
            if "$ref" in node:
                name = node["$ref"].split("/")[-1]
                return walk(copy.deepcopy(definitions[name]))
            node = {key: walk(value) for key, value in node.items() if key != "title"}
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            return node
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(schema)


# ---------------------------------------------------------------------------
# The real Claude client
# ---------------------------------------------------------------------------

# How hard Claude should think for each step. Analysis and hardening benefit
# from more thought; prediction is a quick role-play.
EFFORT_BY_TASK = {
    "analyze": "high",
    "attacks": "high",
    "predict": "medium",
    "judge": "medium",
    "harden": "high",
}


class ClaudeClient:
    """Calls the real Anthropic API."""

    def __init__(self, model: str = config.MODEL):
        if not config.ANTHROPIC_API_KEY:
            raise LLMError(
                "This needs real model answers, so it needs ANTHROPIC_API_KEY in code/.env. "
                "Without a key, only the app's demo mode is available."
            )
        self.model = model
        # The SDK retries rate limits and server errors twice by default.
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def _create(self, task: str, system: str, user: str, output_config: dict):
        """Send one request, turning API errors into readable LLMErrors."""
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config=output_config,
                # If a safety classifier declines (attack text can look
                # suspicious), the API retries on a fallback model for us.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as exc:
            raise LLMError("The API key was rejected. Check ANTHROPIC_API_KEY.") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("Rate limited by the API. Wait a minute and try again.") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Claude API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError("Could not reach the Claude API. Check your internet connection.") from exc

        # Always check why the model stopped before reading the content.
        if response.stop_reason == "refusal":
            raise LLMError(f"Claude declined the '{task}' step.")
        return response

    def structured(self, task: str, system: str, user: str, output_model: type[T]) -> T:
        schema = to_strict_schema(output_model)
        output_config = {
            "effort": EFFORT_BY_TASK.get(task, "medium"),
            "format": {"type": "json_schema", "schema": schema},
        }

        # We try twice: if the first answer fails validation, we ask again once.
        last_problem = ""
        for _attempt in range(2):
            response = self._create(task, system, user, output_config)
            if response.stop_reason == "max_tokens":
                last_problem = "the answer was cut off (max_tokens)"
                continue
            text = "".join(block.text for block in response.content if block.type == "text")
            try:
                return output_model.model_validate_json(text)
            except ValidationError as exc:
                last_problem = f"the JSON did not match the schema: {exc.errors()[:2]}"

        raise LLMError(f"Claude's answer for the '{task}' step was unusable: {last_problem}")

    def text(self, task: str, system: str, user: str) -> str:
        """
        Plain-text answer, with no output schema and no retry.

        The app itself never uses this. It exists so the prompt experiment
        (tools/prompt_experiment.py) can run the older v1 and v2 prompts
        exactly as they were written: they asked for text, not a schema.
        """
        response = self._create(task, system, user, {"effort": "medium"})
        return "".join(block.text for block in response.content if block.type == "text")


# ---------------------------------------------------------------------------
# A fake client for tests
# ---------------------------------------------------------------------------

class FakeLLM:
    """
    A stand-in for Claude used in tests.

    You give it a function per task that returns a dict (or a model). It
    records every call so tests can check what was sent.
    """

    def __init__(self, handlers: dict):
        self.handlers = handlers
        self.calls: list[dict] = []

    def structured(self, task: str, system: str, user: str, output_model: type[T]) -> T:
        self.calls.append({"task": task, "system": system, "user": user})
        result = self.handlers[task](system, user)
        if isinstance(result, BaseModel):
            result = result.model_dump()
        # Validate exactly like the real client does.
        return output_model.model_validate_json(json.dumps(result))

    def text(self, task: str, system: str, user: str) -> str:
        self.calls.append({"task": task, "system": system, "user": user})
        return self.handlers[task](system, user)


def get_llm() -> LLMClient:
    """Pick the right client: demo playback or the real API."""
    if config.DEMO_MODE:
        from app.demo import DemoLLM  # imported here to keep startup light

        return DemoLLM()
    return ClaudeClient()
