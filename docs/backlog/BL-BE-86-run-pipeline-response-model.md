# BL-BE-86: POST /pipeline/run response_model 추가

## 문제

`POST /pipeline/run` 라우터가 `response_model` 없이 dict 를 직접 반환한다.

```python
return {"message": result.message, "processed": result.processed}
```

- OpenAPI 문서에 응답 스키마가 노출되지 않음
- 클라이언트 타입 생성 파이프라인의 근거 없음
- `RunPipelineResult` (유즈케이스 DTO) 와 API 응답 계약이 암묵적으로 분리

## 해결 방안

`RunPipelineResponse(BaseModel)` DTO 를 `run_pipeline_result.py` 에 추가하고,
라우터에 `response_model=RunPipelineResponse` 를 명시한다.

```python
class RunPipelineResponse(BaseModel):
    message: str
    processed: list[dict[str, Any]]
```

## 범위

- `app/domains/pipeline/application/response/run_pipeline_result.py`
- `app/domains/pipeline/adapter/inbound/api/pipeline_router.py`

## 완료 기준

- `POST /pipeline/run` 에 `response_model` 선언
- OpenAPI `/docs` 에 응답 스키마 노출
- 기존 응답 구조 변화 없음
