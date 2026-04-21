# BL-BE-83: RunPipelineUseCase Semaphore 인스턴스 레벨로 이동

## 문제

`_analyze_single_best()` 내부에서 매 호출마다 `asyncio.Semaphore(4)` 를 새로 생성한다.

```python
async def _analyze_single_best(self, raw_articles, symbol, name):
    semaphore = asyncio.Semaphore(_SINGLE_BEST_CONCURRENCY)  # ← 호출마다 독립 생성
```

5심볼 파이프라인 기준 최대 10개의 독립 Semaphore → 최대 40 동시 OpenAI 호출.
`_SINGLE_BEST_CONCURRENCY = 4` 설정의 의도(전체 파이프라인 상한 4)가 무력화된다.

## 해결 방안

`RunPipelineUseCase.__init__` 에서 `self._semaphore = asyncio.Semaphore(_SINGLE_BEST_CONCURRENCY)` 로 생성,
`_analyze_single_best` 에서 `self._semaphore` 참조.

인스턴스 전체에서 하나의 Semaphore 를 공유하므로 전체 동시성이 정책대로 제한된다.

## 범위

- `app/domains/pipeline/application/usecase/run_pipeline_usecase.py`

## 완료 기준

- Semaphore 가 usecase 인스턴스당 1개로 공유됨
- `_SINGLE_BEST_CONCURRENCY` 설정이 전체 파이프라인 단위로 동작
