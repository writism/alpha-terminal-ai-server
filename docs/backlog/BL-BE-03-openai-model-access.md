# BL-BE-03

**Backlog Type**
Behavior Backlog

**Backlog Title**
애플리케이션이 OpenAI 모델 접근 권한 오류를 해결하고 분석을 정상 수행한다

**배경 / 원인**
`gpt-4o-mini` 모델 호출 시 다음 오류 발생:

```
Project proj_uvwhqbcL3BkYjQuXQngaCTZp does not have access to model gpt-4o-mini
```

현재 OpenAI 프로젝트에 `gpt-4o-mini` 접근 권한이 없어 000660(SK하이닉스) 분석이 전체 실패한다.

재현 확인:
- `POST /pipeline/run` → `{"symbol":"000660","skipped":true,"reason":"분석 실패"}`
- OpenAI API 직접 호출 시 위 오류 메시지 반환

**Success Criteria**
- 현재 프로젝트 API 키로 호출 가능한 모델을 사용한다
- 모델 설정이 `.env` 환경변수로 관리되어 코드 수정 없이 변경 가능하다
- 파이프라인 실행 후 `GET /pipeline/summaries`에 000660 분석 결과가 포함된다
- 분석 실패 시 에러 메시지가 로그에 기록된다

**Todo**
1. OpenAI 계정/프로젝트에서 접근 가능한 모델을 확인한다 (예: `gpt-3.5-turbo`, `gpt-4o`)
2. 사용 가능한 모델로 `openai_analyzer_adapter.py`의 모델명을 변경한다
3. 모델명을 하드코딩 대신 `settings.py`의 환경변수(`openai_model`)로 분리한다
4. 파이프라인 재실행 후 000660 분석 결과를 검증한다

**관련 백로그**
- [BL-BE-50](BL-BE-50-llm-responses-infrastructure.md) — Responses API 전용 LLM 인프라 (`openai_responses_model`).
