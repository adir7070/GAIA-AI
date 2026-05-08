"""Smoke tests for prompt templates."""
from app.prompts.judge import JUDGE_PROMPT, RELEVANCE_PROMPT
from app.prompts.runtime import RUNTIME_PROMPT


def test_runtime_prompt_renders():
    out = RUNTIME_PROMPT.format(history="- a\n- b", recent="[IN] hi", incoming="how r u?")
    assert "history" not in out  # placeholder is replaced
    assert "how r u?" in out


def test_judge_prompt_renders():
    out = JUDGE_PROMPT.format(history="hist", incoming="msg", response_a="A1", response_b="B1")
    assert "A1" in out and "B1" in out
    assert "Reply with exactly one character" in out


def test_relevance_prompt_renders():
    out = RELEVANCE_PROMPT.format(incoming="m", response="r")
    assert "1-5" in out
