"""Tests for step 2: analysis."""

from app.examples import EXAMPLE_SYSTEM_PROMPT
from app.llm import FakeLLM
from app.pipeline.analyze import analyze_prompt
from tests.conftest import SAMPLE_ANALYSIS


def test_analysis_renumbers_rules_and_sends_prompt():
    fake = FakeLLM({"analyze": lambda s, u: SAMPLE_ANALYSIS})
    result = analyze_prompt(fake, EXAMPLE_SYSTEM_PROMPT)

    assert [r.id for r in result.rules] == ["R1", "R2"]
    assert result.reads_untrusted_content is True
    # The prompt under test is sent, wrapped in tags.
    assert "<system_prompt_under_test>" in fake.calls[0]["user"]
    assert "CPL-STAFF-4471" in fake.calls[0]["user"]


def test_example_prompt_is_fictional():
    # Only example.com addresses in the built-in example.
    assert "@example.com" in EXAMPLE_SYSTEM_PROMPT
    assert "@gmail" not in EXAMPLE_SYSTEM_PROMPT
