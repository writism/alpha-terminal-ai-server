# BL-BE-50

**Backlog Type**  
Infrastructure / LLM

**Backlog Title**  
LLM 기반 문장 생성 인프라 (OpenAI Responses API + Port + Infrastructure Client)

**Success Criteria**
- OpenAI 모델은 **`gpt-5-mini`** 또는 **`gpt-4.1-mini`** 중 설정으로 사용 (기본값 `gpt-4.1-mini`).
- OpenAI 호출은 **Chat Completions가 아닌 `responses` API** (`client.responses.create`)를 사용한다.
- LLM과 통신하는 **External Client**가 `app/infrastructure/llm`에 위치한다.
- **API Key**는 환경 변수·`Settings`에 등록된다 (`OPENAI_API_KEY`, `OPENAI_RESPONSES_MODEL`).
- **Port**: 프롬프트 문자열을 받아 생성 텍스트 문자열을 반환하는 인터페이스가 `application` 계층에 정의된다.
- **의존성 주입**: 팩토리/게터로 `TextGenerationPort` 구현체를 조립할 수 있다.

**구현 메모**
- 기존 도메인 어댑터(`chat.completions`)는 본 백로그 범위 밖. 신규 경로만 Responses 사용.
- 키·프롬프트 전문은 로그에 남기지 않는다.

**Todo**
1. [x] `OPENAI_RESPONSES_MODEL` + `Settings` 반영, `.env.example` 갱신
2. [x] `TextGenerationPort` (ABC) 정의 — `app/domains/llm/application/usecase/`
3. [x] `OpenAIResponsesTextClient` — `app/infrastructure/llm/`, `responses.create` + `output_text`
4. [x] `get_text_generation_port()` 등 DI 진입점
5. [x] 단위 테스트 (mock `responses.create`)

**관련**
- [BL-BE-03](BL-BE-03-openai-model-access.md) — 모델 접근·설정 맥락
- [BL-BE-51](BL-BE-51-recommendation-reason-llm.md) — 추천 이유 등 Responses 활용 기능

**개정 이력**
- 2026-03-28: 초안 작성 및 구현 완료 (Port, `OpenAIResponsesTextClient`, DI, `Settings`/`OPENAI_RESPONSES_MODEL`, 단위 테스트).
