# Stock Bot

주식 데이터를 수집하고 LLM을 활용하여 투자 리포트를 자동으로 생성하는 텔레그램 봇 및 REST API 서비스입니다.

## 주요 기능

- 📊 **주식 데이터 수집**: yfinance를 통한 실시간 주가 데이터 수집 및 저장
- 📰 **뉴스 수집 및 분석**: 주식 관련 뉴스를 수집하고 벡터 임베딩을 활용한 의미 기반 검색
- 🤖 **AI 리포트 생성**: 다양한 LLM Provider를 지원하는 전문적인 주식 분석 리포트 자동 생성
  - 지원 Provider: Ollama (로컬), Groq, OpenAI, vLLM
  - LangChain Agent를 활용한 동적 데이터 수집 및 분석
- 💾 **리포트 캐싱**: 생성된 리포트를 데이터베이스에 저장하여 중복 생성 방지 및 빠른 조회
- 🔒 **동시성 제어**: 티커별 락을 통한 중복 리포트 생성 방지
- 📱 **텔레그램 봇**: 텔레그램을 통한 간편한 리포트 조회 및 구독 관리
- 🔄 **자동화된 스케줄링**: 평일 오전 9시 자동 데이터 수집 및 리포트 발송
- 🌐 **REST API**: FastAPI 기반의 RESTful API 제공

## 기술 스택

- **언어**: Python 3.12+
- **프레임워크**: FastAPI, python-telegram-bot
- **데이터베이스**: PostgreSQL (pgvector 확장)
- **LLM**: LangChain, 다양한 Provider 지원
  - Ollama (로컬 서버)
  - Groq (고속 추론 API)
  - OpenAI (GPT 모델)
  - vLLM (자체 호스팅 서버)
- **임베딩**: Ollama, OpenAI, vLLM 지원
- **데이터 수집**: yfinance, trafilatura, edgartools (SEC EDGAR)
- **스케줄링**: APScheduler
- **ORM**: SQLAlchemy (비동기)
- **마이그레이션**: Alembic

## 프로젝트 구조

```
stock-bot/
├── alembic/              # 데이터베이스 마이그레이션
├── analysis/             # LLM 분석 모듈
│   └── llm_module.py
├── bot/                  # 텔레그램 봇
│   └── telegram.py
├── collectors/           # 데이터 수집기
│   ├── interfaces/       # 인터페이스 정의
│   ├── news_api.py
│   └── stock_api.py
├── db/                   # 데이터베이스
│   ├── connection.py
│   ├── models.py
│   └── repositories/     # 데이터 접근 계층
├── jobs/                 # 스케줄러 작업
│   └── stock_collector.py
├── routers/              # FastAPI 라우터
│   └── v1.py
├── schemas/              # Pydantic 스키마
│   ├── llm.py            # LLM 관련 스키마 (리포트 등)
│   ├── stock.py          # 주식 관련 스키마
│   └── user.py           # 사용자 관련 스키마
├── services/             # 비즈니스 로직
│   ├── llm_service.py    # LLM 리포트 생성 서비스
│   ├── stock_data_service.py
│   └── user_data_service.py
├── utils/                # 유틸리티 함수
│   └── common.py         # 공통 유틸리티 (타임존, 검증 등)
├── main.py               # 애플리케이션 진입점
├── scheduler.py          # 스케줄러 설정
└── dependencies.py       # 의존성 주입
```

## 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd stock-bot
```

### 2. 의존성 설치

프로젝트는 `uv`를 사용하여 패키지를 관리합니다.

```bash
# uv 설치 (없는 경우)
pip install uv

# 의존성 설치
uv sync
```

### 3. 데이터베이스 설정

PostgreSQL 데이터베이스를 생성하고 pgvector 확장을 활성화합니다.

```sql
CREATE DATABASE stock_bot_db;
\c stock_bot_db;
CREATE EXTENSION vector;
```

### 4. 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 필요한 값들을 설정합니다.

```bash
cp .env.example .env
```

필수 환경 변수:
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰 (@BotFather에서 발급)
- `TELEGRAM_BOT_PASSWORD`: 봇 인증 비밀번호
- `LLM_PROVIDER`: LLM 제공자 (`ollama`, `groq`, `openai`, `vllm` 중 선택)
- `LLM_MODEL`: 사용할 LLM 모델명 (Provider별로 다름)
- `EMBEDDING_PROVIDER`: 임베딩 제공자 (`ollama`, `openai`, `vllm` 중 선택)
- `EMBEDDING_MODEL`: 사용할 임베딩 모델명
- `EDGAR_IDENTITY`: SEC EDGAR API 식별자 (예: "Your Name your.email@example.com")

Provider별 추가 필수 환경 변수:
- **Ollama 사용 시**: `OLLAMA_BASE_URL` (기본값: `http://localhost:11434`)
- **Groq 사용 시**: `GROQ_API_KEY` ([Groq Console](https://console.groq.com/)에서 발급)
- **OpenAI 사용 시**: `OPENAI_API_KEY` ([OpenAI Platform](https://platform.openai.com/api-keys)에서 발급)
- **vLLM 사용 시**: 
  - `VLLM_BASE_URL` (LLM용)
  - `VLLM_EMBEDDING_BASE_URL` (임베딩용)

선택적 환경 변수:
- `BUSINESS_TIMEZONE`: 비즈니스 타임존 (기본값: `Asia/Seoul`). 리포트 생성 시 날짜 결정에 사용됩니다.
- `STOCK_DATA_BATCH_SIZE`: 주가 데이터 배치 크기 (기본값: `5`)
- `STOCK_NEWS_BATCH_SIZE`: 뉴스 배치 크기 (기본값: `3`)
- `BATCH_DELAY_SECONDS`: 배치 간 지연 시간 (기본값: `2.0`)
- `OLLAMA_NUM_GPU`: Ollama 임베딩 모델에 사용할 GPU 개수 (Ollama 기본값 사용 시 생략 가능)
- `HOST`: 서버 호스트 주소 (기본값: `0.0.0.0`)
- `PORT`: 서버 포트 번호 (기본값: `8000`)

전체 환경 변수 목록과 상세 설명은 `.env.example` 파일을 참고하세요.

### 5. 데이터베이스 마이그레이션

```bash
alembic upgrade head
```

### 6. LLM 및 임베딩 모델 설정

선택한 Provider에 따라 모델을 설정합니다.

#### Ollama 사용 시 (로컬 서버)

Ollama를 설치하고 필요한 모델을 다운로드합니다.

```bash
# Ollama 설치 (https://ollama.ai)
ollama pull qwen3:8b          # LLM 모델
ollama pull embeddinggemma    # 임베딩 모델
```

`.env` 파일에서 다음을 설정합니다:
```bash
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=embeddinggemma
```

#### Groq 사용 시 (고속 추론 API)

[Groq Console](https://console.groq.com/)에서 API 키를 발급받고 `.env` 파일에 설정합니다:

```bash
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile
GROQ_API_KEY=your_groq_api_key_here
```

#### OpenAI 사용 시

[OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키를 발급받고 `.env` 파일에 설정합니다:

```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

#### vLLM 사용 시 (자체 호스팅)

vLLM 서버가 실행 중이어야 합니다. `.env` 파일에서 서버 URL을 설정합니다:

```bash
LLM_PROVIDER=vllm
LLM_MODEL=your_model_name
VLLM_BASE_URL=http://your-vllm-server:8000/v1
EMBEDDING_PROVIDER=vllm
EMBEDDING_MODEL=your_embedding_model
VLLM_EMBEDDING_BASE_URL=http://your-vllm-server:8000/v1
```

## 실행

### 개발 모드

```bash
uv run main.py
```

## 사용 방법

### 텔레그램 봇

1. 텔레그램에서 봇을 찾아 시작합니다.
2. `/auth <password>` 명령으로 인증합니다.
3. `/sub <TICKER>` 명령으로 주식 구독을 추가합니다.
4. `/report <TICKER>` 명령으로 리포트를 요청합니다.
5. 구독한 주식에 대한 리포트는 매일 오전 9시(비즈니스 타임존, 기본값: KST)에 자동으로 발송됩니다.

**사용 가능한 명령어:**
- `/auth <password>` - 봇 인증
- `/sub <TICKER>` - 주식 구독 추가
- `/unsub <TICKER>` - 주식 구독 취소
- `/report <TICKER>` - 주식 리포트 생성

### REST API

#### 주식 데이터 수집

```bash
POST /api/v1/collect
Content-Type: application/json

{
  "ticker": "AAPL",
  "period": "1d"
}
```

#### 주식 가격 조회

```bash
GET /api/v1/stock_price?ticker=AAPL
```

#### 주식 뉴스 수집

```bash
POST /api/v1/collect_stock_news
Content-Type: application/json

{
  "ticker": "AAPL"
}
```

#### 주식 뉴스 검색

```bash
GET /api/v1/stock_news?ticker=AAPL&query=earnings
```

#### 사용자 정보 조회

```bash
GET /api/v1/user?provider=telegram&provider_id=<user_id>
```

API 문서는 서버 실행 후 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 스케줄러

스케줄러는 평일 오전 9시(비즈니스 타임존, 기본값: KST)에 다음 작업을 자동으로 수행합니다:

1. 구독된 모든 티커의 주가 데이터 수집
2. 구독된 모든 티커의 뉴스 수집
3. 각 티커에 대한 리포트 생성 및 구독자에게 발송

### 리포트 생성 최적화

- **중복 방지**: 같은 티커에 대해 같은 날짜의 리포트가 이미 존재하면 재생성하지 않고 저장된 리포트를 반환합니다.
- **동시성 제어**: 티커별 락을 사용하여 동시에 여러 요청이 들어와도 중복 생성되지 않습니다.
- **타임존 인식**: 비즈니스 타임존(기본값: `Asia/Seoul`)을 기준으로 날짜를 결정하여 서버 위치와 무관하게 일관된 동작을 보장합니다.

### 배치 처리 설정

배치 처리 설정은 환경 변수로 조정할 수 있습니다:
- `STOCK_DATA_BATCH_SIZE`: 주가 데이터 배치 크기 (기본값: 5)
- `STOCK_NEWS_BATCH_SIZE`: 뉴스 배치 크기 (기본값: 3)
- `BATCH_DELAY_SECONDS`: 배치 간 지연 시간 (기본값: 2.0초)

## 로깅

애플리케이션은 다음 위치에 로그를 저장합니다:

- `logs/stock-bot.log`: 메인 애플리케이션 로그
- `logs/httpx.log`: HTTP 클라이언트 로그
- `logs/httpcore.log`: HTTP 코어 로그

## 개발

### 테스트 실행

```bash
pytest
```

### 데이터베이스 마이그레이션 생성

```bash
uv run alembic revision --autogenerate -m "migration message"
uv run alembic upgrade head
```

## 주요 개선사항

### 다중 LLM Provider 지원

- **유연한 Provider 선택**: Ollama, Groq, OpenAI, vLLM 등 다양한 LLM Provider를 지원합니다.
- **독립적인 임베딩 설정**: LLM과 임베딩 모델을 서로 다른 Provider로 설정할 수 있습니다.
- **환경 변수 기반 설정**: `.env` 파일에서 Provider를 쉽게 변경할 수 있습니다.

### 리포트 관리 시스템

- **데이터베이스 저장**: 생성된 리포트는 `stock_reports` 테이블에 저장되어 재사용됩니다.
- **일일 리포트 제한**: 각 티커당 하루에 하나의 리포트만 생성됩니다 (비즈니스 타임존 기준).
- **캐시 활용**: 같은 날짜의 리포트 요청 시 데이터베이스에서 즉시 반환하여 LLM 호출 비용을 절감합니다.
- **동시성 제어**: 티커별 락을 통한 동시성 제어로 불필요한 리포트 재생성을 방지합니다.

### LangChain Agent 기반 리포트 생성

- **동적 데이터 수집**: LangChain Agent와 Tool을 활용하여 필요한 데이터를 동적으로 수집합니다.
- **SEC EDGAR 통합**: 기업 공시 정보를 자동으로 수집하여 리포트에 반영합니다.
- **전문적인 리포트 형식**: 월스트리트 수준의 구조화된 리포트를 자동 생성합니다.

### 타임존 처리

- 서버의 위치와 무관하게 비즈니스 타임존(기본값: `Asia/Seoul`)을 기준으로 날짜를 결정합니다.
- `BUSINESS_TIMEZONE` 환경 변수를 통해 다른 타임존으로 변경할 수 있습니다.

### 성능 최적화

- 텔레그램 메시지 전송 시 배치 처리(20개씩)를 통해 API 제한을 준수합니다.
- 티커별 락을 통한 동시성 제어로 불필요한 리포트 재생성을 방지합니다.
- 배치 처리 설정을 통한 데이터 수집 최적화.

## 주의사항

⚠️ **면책 조항**: 이 봇이 생성하는 리포트는 투자 조언이 아닙니다. 모든 투자 결정은 사용자의 책임입니다. 투자 전 충분한 조사를 수행하고 전문가의 조언을 구하시기 바랍니다.
