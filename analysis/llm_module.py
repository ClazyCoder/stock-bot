from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import os
from langchain.agents import create_agent
from langchain.tools import BaseTool
from typing import List
import logging
from analysis.prompt_manager import PromptManager


class LLMModule:
    def __init__(self, tools: List[BaseTool]):
        self.logger = logging.getLogger(__name__)
        self.prompt_manager = PromptManager()
        self.main_model = self._build_model()
        self.bullish_agent = create_agent(
            self.main_model, system_prompt=self.prompt_manager.get_prompt("bullish_agent"), tools=tools)
        self.bearish_agent = create_agent(
            self.main_model, system_prompt=self.prompt_manager.get_prompt("bearish_agent"), tools=tools)
        self.moderator_agent = create_agent(
            self.main_model, system_prompt=self.prompt_manager.get_prompt("moderator_agent"))
        self.report_agent = create_agent(
            self.main_model, system_prompt=self.prompt_manager.get_prompt("report_agent"))
        self.logger.info(f"Agent built successfully")

    def _get_model_params(self):
        temperature = os.getenv("LLM_TEMPERATURE", 1.0)
        top_p = os.getenv("LLM_TOP_P", 0.95)
        presence_penalty = os.getenv("LLM_PRESENCE_PENALTY", 1.5)
        return {
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty
        }

    def _build_model(self):
        self.logger.info("Building model...")
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model = os.getenv("LLM_MODEL", "qwen3:8b")
        params = self._get_model_params()
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
                "content": f"Write a report for the following ticker: {ticker}"
            }
        ]
        self.logger.info("Prompt template built successfully")
        bullish_report = await self.bullish_agent.ainvoke({"messages": messages})
        self.logger.info(
            f"Bullish report : {bullish_report['messages'][-1].content}")
        bearish_report = await self.bearish_agent.ainvoke({"messages": messages})
        self.logger.info(
            f"Bearish report : {bearish_report['messages'][-1].content}")

        messages = [
            {
                "role": "user",
                "content": f"Summarize the following reports: {bullish_report['messages'][-1].content} and {bearish_report['messages'][-1].content}"
            }
        ]

        moderator_report = await self.moderator_agent.ainvoke({"messages": messages})
        self.logger.info(
            f"Moderator report : {moderator_report['messages'][-1].content}")
        self.logger.info("Report generated successfully")
        return moderator_report['messages'][-1].content

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
        res = await self.report_agent.ainvoke({"messages": messages})
        self.logger.info(
            f"Report : {res['messages'][-1].content}")
        self.logger.info("Report generated successfully")
        return res['messages'][-1].content
