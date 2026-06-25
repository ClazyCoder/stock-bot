from unittest.mock import patch

import pytest

from analysis.prompt_manager import PromptManager


PROMPT_NAMES = [
    "bullish_agent",
    "bearish_agent",
    "moderator_agent",
    "report_agent",
    "fact_extractor_agent",
    "fact_parser_agent",
]


def test_loads_all_prompts_successfully():
    pm = PromptManager()

    assert pm.bullish_agent_prompt
    assert pm.bearish_agent_prompt
    assert pm.moderator_agent_prompt
    assert pm.report_agent_prompt
    assert pm.fact_extractor_prompt
    assert pm.fact_parser_prompt


def test_get_prompt_known_names_return_strings():
    pm = PromptManager()

    for name in PROMPT_NAMES:
        value = pm.get_prompt(name)
        assert isinstance(value, str)
        assert value


def test_get_prompt_invalid_name_raises():
    pm = PromptManager()

    with pytest.raises(ValueError):
        pm.get_prompt("nonexistent")


def test_reload_keeps_prompts_valid():
    pm = PromptManager()
    pm.reload()

    assert isinstance(pm.bullish_agent_prompt, str)
    assert pm.bullish_agent_prompt


def test_missing_file_raises_runtime_error():
    with patch("builtins.open", side_effect=OSError("not found")):
        with pytest.raises(RuntimeError):
            PromptManager()
