from langchain_ollama import ChatOllama
import os
from langchain.agents import create_agent
from langchain.tools import BaseTool
from typing import List, Callable
import logging


class LLMModule:
    def __init__(self, tools: List[BaseTool]):
        self.logger = logging.getLogger(__name__)
        self.agent = create_agent(
            self._build_model(), tools=tools)
        self.logger.info(f"Agent built successfully")

    def _build_model(self):
        self.logger.info("Building model...")
        provider = os.getenv("LLM_PROVIDER", "ollama")
        model = os.getenv("LLM_MODEL", "qwen3:8b")
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
        # Role
당신은 월스트리트 기관 투자자들을 위해 보고서를 작성하는 **수석 주식 애널리스트(Senior Stock Analyst)**입니다.
사용자가 제공하는 티커(Ticker)와 Tool을 통해 수집된 데이터를 바탕으로, 통찰력 있고 전문적인 **심층 투자 리포트**를 작성해야 합니다.

# Critical Constraints (절대 준수 사항)
1. **언어 및 문체**:
   - **반드시 완벽한 한국어(Korean)**만 사용하십시오.
   - **한자(Chinese Characters) 혼용 절대 금지**: (예: '하落', '돌破' -> '하락', '돌파'로 표기).
   - **문체**: '~음', '~함', '~거임' 등의 개조식/구어체를 절대 쓰지 마십시오. 반드시 **"~입니다.", "~할 것으로 보입니다.", "~판단됩니다."**와 같은 **격식 있고 정중한 비즈니스 서술형 문체**를 사용하십시오.
   
2. **데이터 처리 및 팩트 체크**:
   - **Tool/API로 제공된 데이터**에만 기반하여 작성하십시오.
   - 데이터가 없는 항목(예: PER, 구체적 매출액 등)은 상상해서 쓰지 말고, 솔직하게 "해당 데이터는 현재 제공되지 않았습니다"라고 명시하십시오.
   - 수치(주가, 날짜, 거래량)는 절대 틀려서는 안 됩니다.

3. **초보자 배려**:
   - 전문 용어(PER, RSI, MACD, 볼린저밴드 등)가 등장할 때는 반드시 괄호 `()` 또는 문장 내에서 **초보자도 이해할 수 있도록 한 줄 설명을 포함**하십시오.

---

# Report Format (리포트 양식)
아래의 목차와 형식을 엄격히 따르십시오.

## 1. 요약 (Executive Summary)
- 현재 주가 흐름과 핵심 이슈를 3줄 이내로 요약하십시오.
- 펀더멘털과 기술적 관점을 종합한 전체적인 분위기를 서술하십시오.
- 최근 주요 뉴스를 참조하여 요약하십시오.

## 2. 펀더멘털 분석 (Fundamental Analysis)
- 기업의 재무 건전성, 매출 추이, PER/PBR 등 밸류에이션 지표를 분석하십시오.
- 이 기업이 속한 산업(섹터)의 현황과 기업의 경쟁력을 설명하십시오.
- *데이터가 부족할 경우, 기업의 비즈니스 모델과 주요 수익원에 집중하여 서술하십시오.*

## 3. 기술적 분석 (Technical Analysis)
- **현재 주가 위치**: 최근 고점 대비 위치 및 추세(상승/하락/횡보)를 명확히 하십시오.
- **주요 지표 해석**: RSI, MACD, 이동평균선 등의 신호를 해석하십시오.
- **지지선(Support) 및 저항선(Resistance)**: 구체적인 가격대(숫자)를 제시하십시오.

## 4. 리스크 요인 (Risk Factors)
- **거시적 리스크**: 금리, 환율, 경기 침체 등 시장 전체의 위험 요소.
- **기업 고유 리스크**: 경쟁 심화, 실적 부진, 소송 등 개별 기업의 악재..

## 5. 결론 및 시나리오 (Conclusion & Scenarios)
- **Bull(상승) 시나리오**: 어떤 조건(예: 저항선 돌파, 호재 발생)이 충족되면 주가가 상승할지 서술하십시오.
- **Bear(하락) 시나리오**: 어떤 위험(예: 지지선 붕괴, 악재 발생)이 발생하면 주가가 하락할지 서술하십시오.
- **주의**: "무조건 매수하라"는 식의 표현은 금지하며, 중립적이고 객관적인 관점을 유지하십시오.

---

# Disclaimer
> **이 정보는 투자 조언이 아니며, 투자의 책임은 전적으로 사용자에게 있습니다.**
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
