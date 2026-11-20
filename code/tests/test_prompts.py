"""The final prompt files are generated from code; check every variable is documented and filled."""

import pytest

from app.examples import EXAMPLE_SYSTEM_PROMPT
from app.prompts import analyze_user
from tools.export_prompts import PROMPTS, render, template_variables


@pytest.mark.parametrize("p", PROMPTS, ids=[p["id"] for p in PROMPTS])
def test_every_template_variable_is_documented(p):
    assert template_variables(p["user"]) == list(p["variables"])
    assert p["system"] in render(p)


def test_template_is_filled():
    text = analyze_user(EXAMPLE_SYSTEM_PROMPT)
    assert "{system_prompt}" not in text and "CPL-STAFF-4471" in text
