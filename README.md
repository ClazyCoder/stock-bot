# Stock Bot

주식 데이터와 뉴스를 수집하고, LLM 기반 투자 리포트를 생성해 텔레그램과 API로 제공하는 자동화 서비스입니다.

## 핵심 기능

- 주가 수집: `yfinance` 기반 데이터 수집 및 저장
- 뉴스 수집/청킹: `trafilatura` + configurable chunking(`NEWS_CHUNK_SIZE`, `NEWS_CHUNK_OVERLAP`)
- LLM 리포트 생성: Ollama, Groq, OpenAI, vLLM 지원
- 리포트 캐싱 및 동시성 제어: 티커별 락 + 일자 기준 저장
- 텔레그램 봇: 인증, 구독, 리포트 조회
- 스케줄링: 평일 오전 9시(비즈니스 타임존 기준) 자동 수집/리포트 발송

## 아키텍처 요약

- `FastAPI` API 서버
- `python-telegram-bot` 기반 봇
- `APScheduler` 배치 작업
- `PostgreSQL + pgvector` 저장소

> [!NOTE]
> 앱을 실행하면 API 서버만 뜨는 것이 아니라, 텔레그램 봇과 스케줄러도 함께 시작됩니다.

## 빠른 시작

### 1) 의존성 설치

```bash
pip install uv
uv sync
```

### 2) 환경 변수 파일 생성

```bash
# Linux/macOS
cp .env.example .env

# PowerShell
Copy-Item .env.example .env
```

### 3) 데이터베이스 준비

PostgreSQL DB 생성 후 `pgvector` 확장을 활성화하세요.

```sql
CREATE DATABASE stock_bot_db;
\c stock_bot_db;
CREATE EXTENSION vector;
```

### 4) 마이그레이션

```bash
alembic upgrade head
```

### 5) 실행

```bash
uv run main.py
```

실행 후 문서: `http://localhost:8000/docs`

## 프로젝트 구조

```text
stock-bot/
├── analysis/       # LLM 에이전트 및 프롬프트 처리
├── bot/            # 텔레그램 봇
├── collectors/     # 주가/뉴스 외부 수집
├── db/             # DB 모델/리포지토리/연결
├── jobs/           # 배치 작업(수집/리포트/발송)
├── routers/        # FastAPI 라우터(v1, admin)
├── services/       # 비즈니스 로직
├── main.py         # 앱 진입점(FastAPI + Bot + Scheduler)
└── scheduler.py    # 스케줄 설정
```

## 환경 변수

전체 목록은 `.env.example`을 참고하세요. 아래는 실제 실행에 중요한 항목입니다.

### 필수

- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BOT_PASSWORD`
- `EDGAR_IDENTITY`
- `LLM_PROVIDER`, `LLM_MODEL`
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`

### Provider별 추가 필수

- `LLM_PROVIDER=groq` -> `GROQ_API_KEY`
- `LLM_PROVIDER=openai` -> `OPENAI_API_KEY`
- `LLM_PROVIDER=vllm` -> `VLLM_BASE_URL`
- `EMBEDDING_PROVIDER=openai` -> `OPENAI_API_KEY`
- `EMBEDDING_PROVIDER=vllm` -> `VLLM_EMBEDDING_BASE_URL`

### 운영/튜닝 관련

- 서버/타임존: `HOST`, `PORT`, `BUSINESS_TIMEZONE`
- 배치: `STOCK_DATA_BATCH_SIZE`, `STOCK_NEWS_BATCH_SIZE`, `BATCH_DELAY_SECONDS`
- 뉴스 청킹: `NEWS_CHUNK_SIZE`, `NEWS_CHUNK_OVERLAP`
- Ollama: `OLLAMA_BASE_URL`, `OLLAMA_NUM_GPU`
- 관리자 API 보호: `ADMIN_TOKEN`

> [!WARNING]
> `TELEGRAM_BOT_PASSWORD`가 비어 있으면 앱 시작 시 예외가 발생합니다.

## 텔레그램 사용

- `/auth <password>`: 봇 인증
- `/sub <TICKER>`: 구독 추가
- `/unsub <TICKER>`: 구독 취소
- `/report <TICKER>`: 리포트 요청

## REST API

기본 prefix는 `/api`입니다.

### v1

- `POST /api/v1/collect`
- `GET /api/v1/stock_price?ticker=AAPL`
- `POST /api/v1/collect_stock_news`
- `GET /api/v1/stock_news?ticker=AAPL&query=earnings`
- `GET /api/v1/user?provider=telegram&provider_id=<id>`
- `GET /api/v1/report?ticker=AAPL`

예시:

```bash
curl -X POST "http://localhost:8000/api/v1/collect" \
  -H "Content-Type: application/json" \
  -d "{\"ticker\":\"AAPL\",\"period\":\"1d\"}"
```

```bash
curl "http://localhost:8000/api/v1/report?ticker=AAPL"
```

> [!NOTE]
> `/api/v1/report`는 내부적으로 `force_generate=True`로 호출되어 즉시 새 리포트 생성을 시도합니다.

### Admin

- `GET /api/admin/health_check`
- `POST /api/admin/raw_sql`

> [!WARNING]
> `/api/admin/*` 엔드포인트는 **로컬호스트(127.0.0.1)에서만** 접근 가능합니다. 외부 네트워크에서의 요청은 403으로 거부됩니다.

`/api/admin/*` 호출 시 요청 헤더에 `admin_token`이 필요합니다.

```bash
curl "http://localhost:8000/api/admin/health_check" \
  -H "admin_token: <ADMIN_TOKEN>"
```

## 스케줄러 동작

평일 오전 9시(`BUSINESS_TIMEZONE` 기준)에 다음을 자동 수행합니다.

1. 구독 티커 주가 수집
2. 구독 티커 뉴스 수집
3. 티커별 리포트 생성 및 구독자 전송

## 검증 방법

현재 저장소에는 테스트 파일이 포함되어 있지 않아, 아래 스모크 테스트를 권장합니다.

1. 앱 실행: `uv run main.py`
2. 문서 확인: `http://localhost:8000/docs`
3. v1 API 호출:
   - `GET /api/v1/stock_price?ticker=AAPL`
   - `GET /api/v1/report?ticker=AAPL`
4. admin API 호출:
   - `GET /api/admin/health_check` + `admin_token` 헤더

`pytest`는 의존성에 포함되어 있으므로 테스트 코드 추가 후 다음 명령으로 실행할 수 있습니다.

```bash
pytest
```

## 로깅

- `logs/stock-bot.log`
- `logs/httpx.log`
- `logs/httpcore.log`

## 면책 조항

이 프로젝트가 생성하는 리포트는 투자 자문이 아닙니다. 모든 투자 판단과 책임은 사용자에게 있습니다.
