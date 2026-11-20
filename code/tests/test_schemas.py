"""Tests for the data models and the schema we send to Claude."""

import pytest
from pydantic import ValidationError

from app.llm import FakeLLM, to_strict_schema
from app.schemas import Analysis, Hardening, Judgment


def test_strict_schema_requires_every_field_and_blocks_extras():
    schema = to_strict_schema(Analysis)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    # Nested objects (rules) are inlined and strict too.
    rule_schema = schema["properties"]["rules"]["items"]
    assert "$ref" not in rule_schema
    assert rule_schema["additionalProperties"] is False
    assert "$defs" not in schema


def test_strict_schema_keeps_enums():
    schema = to_strict_schema(Judgment)
    assert schema["properties"]["verdict"]["enum"] == ["Pass", "Fail"]


def test_good_judgment_validates():
    j = Judgment.model_validate(
        {"verdict": "Fail", "severity": "High", "reason": "Leaked prompt", "evidence": "My instructions are"}
    )
    assert j.severity == "High"


def test_bad_judgment_is_rejected():
    with pytest.raises(ValidationError):
        Judgment.model_validate({"verdict": "Maybe", "severity": "High", "reason": "", "evidence": ""})


def test_missing_field_is_rejected():
    with pytest.raises(ValidationError):
        Hardening.model_validate({"fixes": [], "change_summary": []})  # no hardened_prompt


def test_fake_llm_validates_and_records_calls():
    fake = FakeLLM({"judge": lambda s, u: {"verdict": "Pass", "severity": "None", "reason": "ok", "evidence": "no"}})
    result = fake.structured("judge", "sys", "user", Judgment)
    assert result.verdict == "Pass"
    assert fake.calls[0]["task"] == "judge"


def test_field_named_title_is_kept():
    """Regression test (found by test T07): a field called "title" must stay in the schema."""
    fix = to_strict_schema(Hardening)["properties"]["fixes"]["items"]
    assert "title" in fix["properties"] and "title" in fix["required"]
    # Pydantic's descriptive titles are still removed.
    assert "title" not in to_strict_schema(Hardening)
