# Stock Bot

주식 데이터를 수집하고 LLM을 활용하여 투자 리포트를 자동으로 생성하는 텔레그램 봇 및 REST API 서비스입니다.

## 주요 기능

- 📊 **주식 데이터 수집**: yfinance를 통한 실시간 주가 데이터 수집 및 저장
- 📰 **뉴스 수집 및 분석**: 주식 관련 뉴스를 수집하고 벡터 임베딩을 활용한 의미 기반 검색
- 🤖 **AI 리포트 생성**: LLM을 활용한 전문적인 주식 분석 리포트 자동 생성
- 📱 **텔레그램 봇**: 텔레그램을 통한 간편한 리포트 조회 및 구독 관리
- 🔄 **자동화된 스케줄링**: 평일 오전 9시 자동 데이터 수집 및 리포트 발송
- 🌐 **REST API**: FastAPI 기반의 RESTful API 제공

## 기술 스택

- **언어**: Python 3.12+
- **프레임워크**: FastAPI, python-telegram-bot
- **데이터베이스**: PostgreSQL (pgvector 확장)
- **LLM**: LangChain, Ollama (또는 OpenAI, Anthropic)
- **데이터 수집**: yfinance, trafilatura
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
├── services/             # 비즈니스 로직
│   ├── stock_data_service.py
│   └── user_data_service.py
├── utils/                # 유틸리티 함수
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
- `OLLAMA_BASE_URL`: Ollama 서버 URL (LLM 사용 시)
- `LLM_MODEL`: 사용할 LLM 모델명
- `EMBEDDING_MODEL`: 사용할 임베딩 모델명

전체 환경 변수 목록은 `.env.example` 파일을 참고하세요.

### 5. 데이터베이스 마이그레이션

```bash
alembic upgrade head
```

### 6. Ollama 설정 (LLM 사용 시)

Ollama를 설치하고 필요한 모델을 다운로드합니다.

```bash
# Ollama 설치 (https://ollama.ai)
ollama pull qwen3:8b          # LLM 모델
ollama pull embeddinggemma       # 임베딩 모델
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
5. 구독한 주식에 대한 리포트는 매일 오전 9시(KST)에 자동으로 발송됩니다.

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

스케줄러는 평일 오전 9시(KST)에 다음 작업을 자동으로 수행합니다:

1. 구독된 모든 티커의 주가 데이터 수집
2. 구독된 모든 티커의 뉴스 수집
3. 각 티커에 대한 리포트 생성 및 구독자에게 발송

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
alembic revision --autogenerate -m "migration message"
alembic upgrade head
```

## 주의사항

⚠️ **면책 조항**: 이 봇이 생성하는 리포트는 투자 조언이 아닙니다. 모든 투자 결정은 사용자의 책임입니다. 투자 전 충분한 조사를 수행하고 전문가의 조언을 구하시기 바랍니다.
