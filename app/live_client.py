"""
Live mode: send an attack to the user's real chatbot over HTTP.

Every chatbot API looks different, so the user describes theirs:
- url:           where to POST, e.g. http://localhost:8001/chat
- headers:       e.g. {"Authorization": "Bearer ..."} for their own bot
- body_template: JSON with placeholders, e.g. {"message": "{{attack}}"}
                 {{system_prompt}} is also available, for bots that accept one.
- reply_path:    where the reply text is in the response JSON,
                 e.g. "reply" or "choices.0.message.content"

Only point this at chatbots you own or are allowed to test.
"""

import json
from typing import Any

import httpx

from app import config
from app.schemas import LiveConfig


class LiveClientError(Exception):
    """Something went wrong talking to the live chatbot."""


def build_body(template: str, attack_text: str, system_prompt: str) -> Any:
    """
    Fill the placeholders in the body template.

    We parse the template as JSON FIRST and then replace placeholders inside
    the string values. That way quotes or newlines in the attack text can
    never break the JSON.
    """
    try:
        parsed = json.loads(template)
    except json.JSONDecodeError as exc:
        raise LiveClientError(f"The body template is not valid JSON: {exc.msg}") from exc

    def fill(value):
        if isinstance(value, str):
            return value.replace("{{attack}}", attack_text).replace("{{system_prompt}}", system_prompt)
        if isinstance(value, dict):
            return {key: fill(item) for key, item in value.items()}
        if isinstance(value, list):
            return [fill(item) for item in value]
        return value

    if "{{attack}}" not in template:
        raise LiveClientError("The body template must contain {{attack}}.")
    return fill(parsed)


def extract_reply(data: Any, path: str) -> str:
    """Follow a dotted path like 'choices.0.message.content' into the JSON."""
    current = data
    for part in [p for p in path.split(".") if p]:
        try:
            current = current[int(part)] if isinstance(current, list) else current[part]
        except (KeyError, IndexError, ValueError, TypeError):
            raise LiveClientError(f"Could not find '{path}' in the response (stopped at '{part}').")
    if not isinstance(current, str):
        current = json.dumps(current)
    return current


def send_attack(live: LiveConfig, attack_text: str, system_prompt: str = "") -> str:
    """POST one attack to the live endpoint and return the reply text."""
    if not live.url.startswith(("http://", "https://")):
        raise LiveClientError("The endpoint URL must start with http:// or https://")

    body = build_body(live.body_template, attack_text, system_prompt)
    try:
        response = httpx.post(live.url, json=body, headers=live.headers, timeout=config.LIVE_TIMEOUT_SECONDS)
    except httpx.TimeoutException:
        raise LiveClientError(f"The endpoint did not answer within {config.LIVE_TIMEOUT_SECONDS:.0f} seconds.")
    except httpx.HTTPError as exc:
        raise LiveClientError(f"Could not reach the endpoint: {exc}")

    if response.status_code >= 400:
        raise LiveClientError(f"The endpoint returned HTTP {response.status_code}.")
    try:
        data = response.json()
    except ValueError:
        raise LiveClientError("The endpoint did not return JSON.")
    return extract_reply(data, live.reply_path)
