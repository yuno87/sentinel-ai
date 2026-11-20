"""Offline tests for the Gemini client: no network, the SDK call is replaced."""

import importlib
from types import SimpleNamespace

import pytest
from google.genai import errors

from app import config, llm
from app.schemas import Judgment

GOOD = '{"verdict": "Fail", "severity": "High", "reason": "leaked prompt", "evidence": "My rules are"}'


def make_client(monkeypatch, answers):
    """A GeminiClient whose API call returns (or raises) the given answers in order."""
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)  # don't really wait
    client = llm.GeminiClient()
    calls = []

    def fake_generate(model, contents, config):
        calls.append({"model": model, "contents": contents, "config": config})
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return SimpleNamespace(text=answer)

    client.client = SimpleNamespace(models=SimpleNamespace(generate_content=fake_generate))
    return client, calls


def too_many_requests():
    return errors.ClientError(429, {"error": {"code": 429, "message": "Resource exhausted", "status": "RESOURCE_EXHAUSTED"}})


def test_structured_sends_schema_and_system_prompt(monkeypatch):
    client, calls = make_client(monkeypatch, [GOOD])
    result = client.structured("judge", "You are a judge.", "the reply", Judgment)
    assert result.verdict == "Fail"
    settings = calls[0]["config"]
    assert settings.system_instruction == "You are a judge."
    assert settings.response_mime_type == "application/json"
    assert settings.response_json_schema["properties"]["verdict"]["enum"] == ["Pass", "Fail"]


def test_waits_and_retries_when_rate_limited(monkeypatch):
    client, calls = make_client(monkeypatch, [too_many_requests(), too_many_requests(), GOOD])
    assert client.structured("judge", "s", "u", Judgment).severity == "High"
    assert len(calls) == 3


def test_gives_a_clear_error_when_the_limit_never_clears(monkeypatch):
    client, _ = make_client(monkeypatch, [too_many_requests() for _ in range(llm.GeminiClient.MAX_TRIES)])
    with pytest.raises(llm.LLMError, match="free limit"):
        client.structured("judge", "s", "u", Judgment)


def test_retries_once_on_invalid_json(monkeypatch):
    client, calls = make_client(monkeypatch, ['{"verdict": "Maybe"}', GOOD])
    assert client.structured("judge", "s", "u", Judgment).verdict == "Fail"
    assert len(calls) == 2


def test_blocked_answer_is_an_error(monkeypatch):
    client, _ = make_client(monkeypatch, [None])
    with pytest.raises(llm.LLMError, match="declined"):
        client.text("v1", "", "u")


@pytest.mark.parametrize("anthropic, gemini, expected", [
    ("", "", "demo"), ("", "g-key", "gemini"), ("a-key", "g-key", "claude"), ("a-key", "", "claude"),
])
def test_provider_follows_whichever_key_is_set(monkeypatch, anthropic, gemini, expected):
    monkeypatch.setenv("ANTHROPIC_API_KEY", anthropic)
    monkeypatch.setenv("GEMINI_API_KEY", gemini)
    monkeypatch.delenv("SENTINEL_DEMO", raising=False)
    try:
        importlib.reload(config)
        assert config.PROVIDER == expected
        assert config.DEMO_MODE is (expected == "demo")
    finally:
        monkeypatch.undo()
        importlib.reload(config)
