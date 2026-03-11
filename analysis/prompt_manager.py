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
        elif prompt_name == "fact_extractor_agent":
            return self.fact_extractor_prompt
        elif prompt_name == "fact_parser_agent":
            return self.fact_parser_prompt
        else:
            raise ValueError(f"Invalid prompt name: {prompt_name}")

    def _load_prompts(self) -> None:
        base_dir = os.path.join(os.path.dirname(__file__), "prompts")
        prompts = {
            "bullish_agent_prompt": "bullish_agent.md",
            "bearish_agent_prompt": "bearish_agent.md",
            "moderator_agent_prompt": "moderator_agent.md",
            "report_agent_prompt": "report_agent.md",
            "fact_extractor_prompt": "fact_extractor.md",
            "fact_parser_prompt": "fact_parser.md"
        }

        for attr_name, filename in prompts.items():
            path = os.path.join(base_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    setattr(self, attr_name, file.read())
            except OSError as exc:
                self.logger.error(
                    "Failed to load prompt '%s' from '%s': %s",
                    attr_name,
                    path,
                    exc,
                )
                raise RuntimeError(
                    f"Failed to load prompt file '{path}'") from exc
        self.logger.info("Prompts loaded successfully")

    def reload(self) -> None:
        self._load_prompts()
        self.logger.info("Prompts reloaded successfully")
