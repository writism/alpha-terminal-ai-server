# 2026-04-21 백엔드 리팩토링 — 성능 · 타입

> 교차 저장소 리포트: [../../docs/REFACTORING-20260421-PERF-AND-TYPES.md](../../docs/REFACTORING-20260421-PERF-AND-TYPES.md)

## 핵심 변경

1. **OpenAI async 전환** — 5개 어댑터(`openai_analyzer_adapter.py`, `openai_sentiment_adapter.py`, `openai_risk_tag_adapter.py`, `openai_keyword_adapter.py`, `news_search/openai_analysis_adapter.py`) 모두 `AsyncOpenAI` + `await`. 이벤트 루프 블로킹 제거.
2. **`/news/search` 스레드풀 오프로드** — `run_in_threadpool(usecase.execute, ...)`. `SerpClient` 는 프로세스 공용 `httpx.Client` (커넥션 풀) 재사용.
3. **파이프라인 상태 저장소 포트/어댑터** — `ProgressStorePort` / `SummaryRegistryPort` 신설. in-memory + Redis 어댑터, `pipeline_state_redis_enabled` 설정 기반 팩토리. 멀티 워커 안전.
4. **단건 분석 병렬화** — `_analyze_single_best` 를 `asyncio.gather` + `Semaphore(4)` 로 전환.
5. **타입 경계 강화** — `RunPipelineUseCase.execute` 반환을 Pydantic `RunPipelineResult` 로 교체. `ArticleContentStorePort` 의 `Dict[str, Any]` 를 `ArticleRawData` TypedDict 로.
6. **pyright 도입** — 루트에 `pyproject.toml` (`basic`), CI `typecheck` 잡(`continue-on-error`).
7. **정리** — `log_context` 중복을 infra 쪽으로 통합, 스케줄러 `run_pipeline_job` 이 유즈케이스 직접 호출, `session_scope()` / `pg_session_scope()` 컨텍스트 매니저 도입 및 `investment_router` 임시 세션 일관화.

## 신규 파일

- `app/domains/pipeline/application/usecase/summary_registry_port.py`
- `app/domains/pipeline/application/usecase/progress_store_port.py`
- `app/domains/pipeline/application/response/run_pipeline_result.py`
- `app/domains/pipeline/adapter/outbound/state/{__init__,factory,in_memory_summary_registry,in_memory_progress_store,redis_summary_registry,redis_progress_store}.py`
- `pyproject.toml`

## 설정

- `pipeline_state_redis_enabled: bool = True` (Redis PING 실패 시 in-memory 폴백)

## 운영 메모

- 멀티 워커 배포(`uvicorn --workers 2+`) 를 쓰려면 Redis 가 필요.
- Redis 키:
  - `pipeline:summary:{account_id}` HASH, TTL 24h
  - `pipeline:progress:{account_id}` LIST, TTL 1h

## 검증 체크리스트

- `pytest` 통과 (CI)
- `/news/search` p50 전/후 비교
- 5심볼 파이프라인 총 실행시간 전/후 비교
- 워커 2개 기동 후 `/pipeline/run-stream` → `/pipeline/summaries` 일관성 확인
