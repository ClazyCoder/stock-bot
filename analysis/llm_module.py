from langchain_ollama import ChatOllama
import os
from langchain.agents import create_agent
from typing import List, Callable
from langchain.tools import tool
import logging


class LLMModule:
    def __init__(self, tool_func_list: List[Callable]):
        self.logger = logging.getLogger(__name__)
        tools = [tool(func) for func in tool_func_list]
        self.agent = create_agent(
            self._build_model(), tools=tools)
        self.logger.info(f"Agent built successfully")

    def _build_model(self):
        self.logger.info("Building model...")
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model = os.getenv("LLM_MODEL", "qwen_stock")
        if provider == "ollama":
            return ChatOllama(model=model, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        elif provider == "openai":
            # TODO: Implement OpenAI model
            raise NotImplementedError("OpenAI model is not implemented")
        elif provider == "anthropic":
            # TODO: Implement Anthropic model
            raise NotImplementedError("Anthropic model is not implemented")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_report_with_ticker(self, ticker: str) -> str:
        """
        Generate a report for a given ticker.
        """
        self.logger.info(f"Generating report for {ticker}...")
        prompt = f"""
        유저가 제공하는 티커에 대해 종합적인 주식 리포트를 작성하세요.

        # 작성 방식
        - 반드시 한국어로 작성하세요.
        - 최신 데이터와 주어진 정보(도구, API 등)를 우선 활용하세요.
        - 각 항목을 명확하게 구분해서 Markdown 형태(굵은 제목, 표 등 사용)로 작성하세요.

        # 리포트 양식(필수)
        **요약 (3줄 이내 / Executive Summary)**  
        **펀더멘털 분석**  
        - 매출, 영업이익, PER 등 주요 재무 지표와 기업 특성 설명  
        **기술적 분석**  
        - 차트 패턴, 지지/저항선, RSI/MACD 등 주요 지표 해석  
        **리스크 요인**  
        - 해당 종목 및 시장의 주요 위험 요소  
        **결론 및 시나리오**  
        - Bull(상승) / Bear(하락) 시나리오를 동시에 제시하며 단정적 매수/매도 표현은 피함

        # 추가 조건
        - 투자 권유 금지: "매수/매도하세요" 대신 중립적·분석적으로 표현
        - 전문 용어(PER, RSI, MACD 등)가 나오면 초보자에게 한 줄로 설명
        - 마지막엔 “이 정보는 투자 조언이 아니며, 투자의 책임은 전적으로 사용자에게 있습니다.” 문구 필수 포함
        """
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": f"다음 티커에 대한 주식 리포트를 작성하세요: {ticker}"
            }
        ]
        self.logger.info("Prompt template built successfully")
        res = await self.agent.ainvoke({"messages": messages})
        self.logger.info(res)
        self.logger.info("Report generated successfully")
        return res['messages'][-1].content
