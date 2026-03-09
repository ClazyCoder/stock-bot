import logging
import os


class PromptManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_prompts()

    def get_prompt(self, prompt_name: str) -> str:
        if prompt_name == "bullish_agent":
            return self.bullish_agent_prompt
        elif prompt_name == "bearish_agent":
            return self.bearish_agent_prompt
        elif prompt_name == "moderator_agent":
            return self.moderator_agent_prompt
        elif prompt_name == "report_agent":
            return self.report_agent_prompt
        else:
            raise ValueError(f"Invalid prompt name: {prompt_name}")

    def _load_prompts(self) -> None:
        with open(os.path.join(os.path.dirname(__file__), "prompts", "bullish_agent.md"), "r", encoding="utf-8") as file:
            self.bullish_agent_prompt = file.read()
        with open(os.path.join(os.path.dirname(__file__), "prompts", "bearish_agent.md"), "r", encoding="utf-8") as file:
            self.bearish_agent_prompt = file.read()
        with open(os.path.join(os.path.dirname(__file__), "prompts", "moderator_agent.md"), "r", encoding="utf-8") as file:
            self.moderator_agent_prompt = file.read()
        with open(os.path.join(os.path.dirname(__file__), "prompts", "report_agent.md"), "r", encoding="utf-8") as file:
            self.report_agent_prompt = file.read()
        self.logger.info("Prompts loaded successfully")

    def reload(self) -> None:
        self._load_prompts()
        self.logger.info("Prompts reloaded successfully")
