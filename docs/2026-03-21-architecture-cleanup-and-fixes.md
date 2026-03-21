# 2026-03-21 아키텍처 정리 및 버그 수정

작업자: 이승욱
기준 문서: `CLAUDE.md`, `/Users/sulee/dev/codelab/FIXLIST.md`

---

## 1. 아키텍처 위반 수정 (CLAUDE.md 기준)

### VIOLATION 1 — Application Layer에서 FastAPI HTTPException 사용

**규칙**: Application Layer는 FastAPI를 import하면 안 된다.

#### 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `watchlist/application/usecase/add_watchlist_usecase.py` | `HTTPException(409)` → `ValueError("이미 등록된 종목입니다.")` |
| `watchlist/application/usecase/remove_watchlist_usecase.py` | `HTTPException(404)` → `ValueError("관심종목을 찾을 수 없습니다.")` |
| `news_search/application/usecase/save_article_usecase.py` | `HTTPException(409)` → `ValueError("이미 저장된 기사입니다.")` |
| `news_analyzer/application/usecase/analyze_article_usecase.py` | `HTTPException(404/422)` → `ArticleNotFoundError` / `EmptyContentError` (커스텀 예외) |

#### 신규 파일

- `news_analyzer/application/usecase/exceptions.py`
  ```python
  class ArticleNotFoundError(ValueError): pass
  class EmptyContentError(ValueError): pass
  ```

#### Router 변경 (예외 변환 추가)

| 파일 | 변경 내용 |
|------|-----------|
| `watchlist/adapter/inbound/api/watchlist_router.py` | `add_watchlist`: `ValueError` → `HTTPException(409)` / `remove_watchlist`: `ValueError` → `HTTPException(404)` |
| `news_search/adapter/inbound/api/saved_article_router.py` | `save_article`: `ValueError` → `HTTPException(409)` |
| `news_analyzer/adapter/inbound/api/news_analyzer_router.py` | `ArticleNotFoundError` → `HTTPException(404)` / `EmptyContentError` → `HTTPException(422)` |

---

### VIOLATION 2 — Router에 비즈니스 로직 포함

**규칙**: Router에는 비즈니스 로직을 작성하면 안 된다.

#### 수정 전

`pipeline_router.py`의 `run_pipeline()` 핸들러에 80줄짜리 수집→정규화→분석 루프 로직이 직접 구현되어 있었다.

#### 수정 후

**신규 파일**: `pipeline/application/usecase/run_pipeline_usecase.py`

```
RunPipelineUseCase.__init__(
    watchlist_repository,
    raw_article_repository,
    collectors,
    normalize_usecase,
    analysis_usecase,
)
RunPipelineUseCase.execute() → {"message", "processed", "summaries"}
```

**`pipeline_router.py`** 역할 축소:
1. 의존성 생성 및 UseCase 주입
2. `usecase.execute()` 호출
3. `_summary_registry` 업데이트
4. 응답 반환

---

### VIOLATION 3 — Router 파일에 Pydantic 모델 정의

**규칙**: Request/Response DTO는 Application Layer(`application/response/`)에 위치해야 한다.

#### 수정 내용

- `pipeline_router.py` 내 `class StockSummary(BaseModel)` 제거
- **신규 파일**: `pipeline/application/response/stock_summary_response.py`
  ```python
  class StockSummaryResponse(BaseModel):
      symbol: str
      name: str
      summary: str
      tags: list
      sentiment: str
      sentiment_score: float
      confidence: float
  ```

---

## 2. FIXLIST.md 항목 적용

### BE-01 (P0) — OpenAI API 잘못된 호출 방식

**영향**: 뉴스 분석, 주식 분석, Pipeline 실행 시 `AttributeError` 즉시 발생

| 파일 | 변경 내용 |
|------|-----------|
| `news_search/adapter/outbound/external/openai_analysis_adapter.py` | `responses.create` + `gpt-5-mini` → `chat.completions.create` + `gpt-4o-mini` |
| `stock_analyzer/adapter/outbound/external/openai_analyzer_adapter.py` | 동일 |

```python
# 변경 전
response = self._client.responses.create(model="gpt-5-mini", input=prompt)
raw = response.output_text.strip()

# 변경 후
response = self._client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)
raw = response.choices[0].message.content.strip()
```

---

### BE-02 (P0) — 회원가입 후 `account_id` 쿠키 미세팅

**영향**: 신규 회원가입 직후 인증 상태가 `UNAUTHENTICATED`로 유지됨

**파일**: `account/adapter/inbound/api/account_router.py`

```python
# 추가
response.set_cookie(key="account_id", value=str(result.account_id), max_age=3600, samesite="lax")
```

프론트 `getCurrentUserFromCookie()`는 `nickname`, `email`, `account_id` 세 쿠키가 모두 있어야 `AuthUser`를 반환한다. 기존 회원 로그인(`kakao_authentication_router.py`)은 이미 세팅 중이었으나 신규 회원가입 경로에 누락되어 있었다.

---

### BE-03 (P0) — `.env` git 추적

**확인 결과**: `.gitignore`에 이미 `.env` 등록되어 있고 `git ls-files .env` 결과 없음 → 이미 안전.

---

### BE-05 (P1) — `account_router.py` 내부 예외 메시지 클라이언트 노출

**파일**: `account/adapter/inbound/api/account_router.py`

```python
# 변경 전
raise HTTPException(status_code=500, detail=f"계정 생성 실패: {e}")

# 변경 후
logging.getLogger(__name__).exception("계정 생성 중 오류 발생")
raise HTTPException(status_code=500, detail="내부 오류가 발생했습니다.")
```

---

### BE-06 (P1) — Pipeline 동기/비동기 혼용

**파일**: `pipeline/application/usecase/run_pipeline_usecase.py`

`async def execute()` 내부에서 `collect_usecase.execute(symbol)` 동기 호출이 이벤트 루프를 블로킹했다.

```python
# 변경 전
collect_usecase.execute(symbol)

# 변경 후
await asyncio.to_thread(collect_usecase.execute, symbol)
```

---

### BE-07 (P2) — `print()` 디버그 코드 → logging

| 파일 | 변경 내용 |
|------|-----------|
| `kakao_auth/application/usecase/check_kakao_user_registration_usecase.py` | `print(...)` → `logger.debug(...)` |
| `kakao_auth/application/usecase/check_kakao_account_registration_usecase.py` | `print(...)` → `logger.debug(...)` |

---

### BE-08 (P2) — Pipeline Silent Exception

`run_pipeline_usecase.py` 작성 시점에 이미 `logger.warning(f"[Pipeline] {symbol} 기사 분석 실패: {e}")` 포함됨 → 별도 수정 불필요.

---

### BE-09 (P2) — `asyncio.gather` return_exceptions 미사용

**파일**: `news_search/application/usecase/bulk_analyze_usecase.py`

```python
# 변경 전
items = await asyncio.gather(*tasks)
results = [item for item in items if item is not None]

# 변경 후
items = await asyncio.gather(*tasks, return_exceptions=True)
results = [item for item in items if isinstance(item, BulkAnalyzeItem)]
```

`return_exceptions=True` 설정 시 개별 태스크 실패가 전체 gather를 취소하지 않는다. `isinstance` 필터로 예외 객체를 명시적으로 제거한다.

---

### BE-10 (P2) — `kakao_client_secret` 토큰 교환 미사용

카카오 앱 설정에서 `Client Secret` 사용 여부를 확인한 후 필요 시 `kakao_token_adapter.py` POST 바디에 추가한다. 현재 앱 설정에서 비활성화된 경우 불필요.

> **미적용** — 카카오 앱 설정 확인 후 별도 적용 필요

---

### BE-11 (P3) — OpenAI Adapter 매 요청마다 재생성

**파일**: `news_search/adapter/inbound/api/saved_article_router.py`

```python
# 변경 전: 요청마다 새 인스턴스
analysis_port = OpenAIAnalysisAdapter(api_key=get_settings().openai_api_key)

# 변경 후: 모듈 레벨에서 한 번만 생성
_settings = get_settings()
_analysis_adapter = OpenAIAnalysisAdapter(api_key=_settings.openai_api_key)
```

---

## 3. ISSUE-01 백엔드 수정 (신규 회원 redirect)

프론트엔드 `ISSUE-01-temp-token-httonly.md` 요청 사항 대응.

**파일**: `kakao_auth/adapter/inbound/api/kakao_authentication_router.py`

| 분기 | 변경 전 | 변경 후 |
|------|---------|---------|
| 신규 회원 | `HTTP 200 JSONResponse` | `HTTP 302 → /auth-callback?nickname=...&email=...` + `temp_token` HttpOnly Cookie |
| 기존 회원 | `HTTP 302 → /` + 쿠키 | 변경 없음 (기존 정상) |

프론트 URL: `settings.cors_allowed_frontend_url` 재사용 (신규 환경변수 추가 불필요).

---

## 수정 파일 목록

| 파일 | 분류 |
|------|------|
| `watchlist/application/usecase/add_watchlist_usecase.py` | VIOLATION 1 |
| `watchlist/application/usecase/remove_watchlist_usecase.py` | VIOLATION 1 |
| `news_search/application/usecase/save_article_usecase.py` | VIOLATION 1 |
| `news_analyzer/application/usecase/analyze_article_usecase.py` | VIOLATION 1 |
| `news_analyzer/application/usecase/exceptions.py` *(신규)* | VIOLATION 1 |
| `watchlist/adapter/inbound/api/watchlist_router.py` | VIOLATION 1 |
| `news_search/adapter/inbound/api/saved_article_router.py` | VIOLATION 1, BE-11 |
| `news_analyzer/adapter/inbound/api/news_analyzer_router.py` | VIOLATION 1 |
| `pipeline/application/response/stock_summary_response.py` *(신규)* | VIOLATION 3 |
| `pipeline/application/usecase/run_pipeline_usecase.py` *(신규)* | VIOLATION 2, BE-06 |
| `pipeline/adapter/inbound/api/pipeline_router.py` | VIOLATION 2, 3 |
| `news_search/adapter/outbound/external/openai_analysis_adapter.py` | BE-01 |
| `stock_analyzer/adapter/outbound/external/openai_analyzer_adapter.py` | BE-01 |
| `account/adapter/inbound/api/account_router.py` | BE-02, BE-05 |
| `kakao_auth/application/usecase/check_kakao_user_registration_usecase.py` | BE-07 |
| `kakao_auth/application/usecase/check_kakao_account_registration_usecase.py` | BE-07 |
| `news_search/application/usecase/bulk_analyze_usecase.py` | BE-09 |
| `kakao_auth/adapter/inbound/api/kakao_authentication_router.py` | ISSUE-01 |
