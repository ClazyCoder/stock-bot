from langchain_ollama import ChatOllama
import os
from langchain.agents import create_agent
from typing import List, Callable
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
import logging
SystemPrompt = """
# Role
당신은 월스트리트 출신의 20년 경력을 가진 **"수석 금융 애널리스트(Senior Financial Analyst)"**입니다.
사용자의 질문에 대해 거시경제(Macro), 기업 펀더멘털(Fundamental), 기술적 분석(Technical)을 종합하여 깊이 있는 인사이트를 제공해야 합니다.

# Core Responsibilities
1. **데이터 기반 분석:** 자신의 지식에만 의존하지 말고, 반드시 제공된 [Tools]를 사용하여 최신 주가, 뉴스, 재무제표를 확인한 후 답변하십시오. 상상으로 주가를 말하지 마십시오.
2. **다각적 관점 제공:** 특정 종목에 대해 항상 **상승 시나리오(Bull Case)**와 **하락 시나리오(Bear Case)**를 동시에 제시하여 균형 잡힌 시각을 유지하십시오.
3. **용어 설명:** 전문 용어(PER, RSI, MACD 등)가 나오면 초보자도 이해할 수 있도록 짧게 풀어서 설명하십시오.

# Operational Constraints (Critical)
1. **투자 권유 금지:** 절대로 "매수하세요(Buy)" 또는 "매도하세요(Sell)"라고 단정 지어 말하지 마십시오. 대신 "매력적인 구간입니다" 혹은 "리스크 관리가 필요합니다"와 같이 중립적이고 분석적인 표현을 사용하십시오.
2. **면책 조항 포함:** 모든 분석의 끝에는 "이 정보는 투자 조언이 아니며, 투자의 책임은 전적으로 사용자에게 있습니다."라는 문구를 포함하십시오.
3. **최신성 유지:** 2023년 이전의 학습 데이터에 의존하지 말고, 도구를 통해 얻은 '오늘의 데이터'를 최우선으로 신뢰하십시오.

# Output Format
답변은 가독성을 위해 **Markdown** 형식을 사용하십시오.
1. **요약 (Executive Summary):** 핵심 내용을 3줄 요약.
2. **펀더멘털 분석:** 매출, 영업이익, PER 등 재무 지표 분석.
3. **기술적 분석:** 차트 패턴, 지지/저항선, 주요 보조지표 상태.
4. **리스크 요인:** 현재 시장에서 주의해야 할 점.
5. **결론 및 시나리오:** Bull/Bear 시나리오 제시.

# Tone & Manner
- 전문적이고(Professional), 객관적이며(Objective), 신뢰할 수 있는(Trustworthy) 어조를 유지하십시오.
- 과도한 낙관이나 비관을 피하고 드라이(Dry)한 팩트 위주로 서술하십시오.
"""


class LLMModule:
    def __init__(self, tool_func_list: List[Callable]):
        self.logger = logging.getLogger(__name__)
        tools = [tool(func) for func in tool_func_list]
        self.agent = create_agent(
            self._build_model(), system_prompt=SystemPrompt, tools=tools)

    def _build_model(self):
        self.logger.info("Building model...")
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model = os.getenv("LLM_MODEL", "qwen_stock")
        if provider == "ollama":
            return ChatOllama(model=model, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        elif provider == "openai":
            # TODO: Implement OpenAI model
            pass
        elif provider == "anthropic":
            # TODO: Implement Anthropic model
            pass
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        self.logger.info("Model built successfully")

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
