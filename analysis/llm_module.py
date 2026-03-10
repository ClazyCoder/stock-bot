from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import asyncio
import os
from langchain.agents import create_agent
from langchain.tools import BaseTool
from typing import List
import logging
import time
from analysis.prompt_manager import PromptManager
from schemas.langchain import FactExtractionResult


class LLMModule:
    def __init__(self, stock_tools: List[BaseTool], edgar_tools: List[BaseTool]):
        self.logger = logging.getLogger(__name__)
        self.prompt_manager = PromptManager()
        self.main_model = self._build_model(self._get_model_params())
        self.fact_extractor_model = self._build_model(
            {"temperature": 0.0, "top_p": 0.95, "presence_penalty": 1.5})
        self.debate_model = self._build_model(
            {"temperature": 0.7, "top_p": 0.95, "presence_penalty": 1.5})
        self.fact_extractor_agent = create_agent(
            self.fact_extractor_model, system_prompt=self.prompt_manager.get_prompt("fact_extractor_agent"), tools=edgar_tools, response_format=FactExtractionResult)
        self.bullish_agent = create_agent(
            self.debate_model, system_prompt=self.prompt_manager.get_prompt("bullish_agent"), tools=stock_tools)
        self.bearish_agent = create_agent(
            self.debate_model, system_prompt=self.prompt_manager.get_prompt("bearish_agent"), tools=stock_tools)
        self.moderator_agent = create_agent(
            self.fact_extractor_model, system_prompt=self.prompt_manager.get_prompt("moderator_agent"))
        self.report_agent = create_agent(
            self.main_model, system_prompt=self.prompt_manager.get_prompt("report_agent"))
        self.logger.info("All agents built successfully")

    def _get_model_params(self):
        try:
            temperature = float(os.getenv("LLM_TEMPERATURE", "1.0"))
            top_p = float(os.getenv("LLM_TOP_P", "0.95"))
            presence_penalty = float(os.getenv("LLM_PRESENCE_PENALTY", "1.5"))
        except ValueError:
            self.logger.error(
                "Invalid LLM_TEMPERATURE, LLM_TOP_P, or LLM_PRESENCE_PENALTY environment variables. Using default values.")
            temperature = 1.0
            top_p = 0.95
            presence_penalty = 1.5
        return {"temperature": temperature, "top_p": top_p, "presence_penalty": presence_penalty}

    def _build_model(self, params: dict):
        self.logger.info("Building model... with params: %s", params)
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model = os.getenv("LLM_MODEL", "qwen3:8b")
        if provider == "ollama":
            return ChatOllama(model=model, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        elif provider == "groq":
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key or not groq_api_key.strip():
                self.logger.error(
                    "GROQ_API_KEY environment variable is not set but 'groq' provider was selected.")
                raise ValueError(
                    "GROQ_API_KEY environment variable must be set when using the 'groq' provider.")
            return ChatGroq(model=model, api_key=groq_api_key)
        elif provider == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key or not openai_api_key.strip():
                self.logger.error(
                    "OPENAI_API_KEY environment variable is not set or is empty but 'openai' provider was selected.")
                raise ValueError(
                    "OPENAI_API_KEY environment variable must be set to a non-empty value when using the 'openai' provider.")
            return ChatOpenAI(model=model, api_key=openai_api_key, **params)
        elif provider == "vllm":
            vllm_base_url = os.getenv("VLLM_BASE_URL")
            if not vllm_base_url or not vllm_base_url.strip():
                self.logger.error(
                    "VLLM_BASE_URL environment variable is not set but 'vllm' provider was selected.")
                raise ValueError(
                    "VLLM_BASE_URL environment variable must be set when using the 'vllm' provider.")
            return ChatOpenAI(model=model, api_key="", base_url=vllm_base_url, **params)
        elif provider == "anthropic":
            # TODO: Implement Anthropic model
            raise NotImplementedError("Anthropic model is not implemented")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _generate_report(self, ticker: str) -> str:
        """
        Generate a report for a given ticker.
        """
        messages = [
            {
                "role": "user",
                "content": f"Extract canonical financial and market facts from the provided source textfor the following ticker: {ticker}"
            }
        ]
        raw_fact_extraction_result = await self.fact_extractor_agent.ainvoke({"messages": messages})
        fact_extraction_result = raw_fact_extraction_result["structured_response"]
        self.logger.info(
            "Fact extraction result: %s", fact_extraction_result.model_dump_json())
        self.logger.info(
            "Invoking bullish and bearish agents concurrently with initial ticker prompt")
        messages = [
            {
                "role": "user",
                "content": f"Write a report for the following ticker: {ticker} and the following facts: {fact_extraction_result.model_dump_json()}"
            }
        ]
        bullish_report, bearish_report = await asyncio.gather(
            self.bullish_agent.ainvoke({"messages": messages}),
            self.bearish_agent.ainvoke({"messages": messages}),
        )
        bullish_content = bullish_report['messages'][-1].content
        bearish_content = bearish_report['messages'][-1].content
        self.logger.info(
            "Bullish agent completed: ticker=%s, chars=%d",
            ticker, len(bullish_content))
        self.logger.info(
            "Bearish agent completed: ticker=%s, chars=%d",
            ticker, len(bearish_content))
        messages = [
            {
                "role": "user",
                "content": f"Summarize the following reports: {bullish_content} and {bearish_content}"
            }
        ]

        moderator_start_time = time.monotonic()
        moderator_report = await self.moderator_agent.ainvoke({"messages": messages})
        moderator_elapsed = time.monotonic() - moderator_start_time
        moderator_content = moderator_report['messages'][-1].content
        self.logger.info(
            "Moderator agent completed: ticker=%s, chars=%d, elapsed=%.2fs",
            ticker, len(moderator_content), moderator_elapsed)
        self.logger.debug("Moderator report content: %s", moderator_content)
        self.logger.info(
            "Intermediate report generated successfully for ticker=%s", ticker)
        return moderator_content

    async def generate_report_with_ticker(self, ticker: str) -> str:
        """
        Generate a report for a given ticker.
        """
        self.logger.info(f"Generating report for {ticker}...")
        report = await self._generate_report(ticker)
        messages = [
            {
                "role": "user",
                "content": f"다음 종합 리포트를 한국어로 번역하세요: {report}"
            }
        ]
        self.logger.info("Prompt template built successfully")
        report_start_time = time.monotonic()
        res = await self.report_agent.ainvoke({"messages": messages})
        report_elapsed = time.monotonic() - report_start_time
        final_content = res['messages'][-1].content
        self.logger.info(
            "Final report agent completed: ticker=%s, chars=%d, elapsed=%.2fs",
            ticker, len(final_content), report_elapsed)
        self.logger.debug("Final report content: %s", final_content)
        self.logger.info("Report generated successfully for ticker=%s", ticker)
        return final_content
