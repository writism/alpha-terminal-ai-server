# BL-BE-51

**Backlog Type**  
Feature / stock_theme + LLM

**Backlog Title**  
키워드·테마 기반 추천 이유 문장 생성 (OpenAI Responses API, gpt-5-mini)

**Success Criteria**
- 각 추천 종목에 대해 **매칭된 키워드(분석 키워드와 종목 테마의 교집합)** 및 **종목 등록 테마** 맥락을 반영한 추천 이유 문장을 생성한다.
- 추천 이유 생성은 **OpenAI Responses API** (`client.responses.create`, BL-BE-50 Port)를 사용한다.
- 해당 경로의 모델은 **`gpt-5-mini`** (`OPENAI_RECOMMENDATION_REASON_MODEL`, 기본값 동일).
- 응답 DTO에 종목별 **`recommendation_reason`** 필드를 포함한다.
- 문장은 사용자가 이해하기 쉬운 **한국어 자연어**이며, 어떤 키워드가 어떤 테마 맥락과 연결되는지 드러난다.
- API 키가 없거나 LLM 출력 파싱에 실패한 경우 **규칙 기반 폴백 문장**으로 응답 무결성을 유지한다 (운영·로컬 개발).

**Todo**
1. [x] 매칭 결과 + 테마 맥락으로 프롬프트를 구성하는 **프롬프트 템플릿** 정의
2. [x] **Domain Service** (`RecommendationReasonGenerationService`) — Port 호출·JSON 파싱·폴백
3. [x] `RecommendationItem`에 `recommendation_reason` 추가
4. [x] `RecommendStocksUseCase`에 이유 생성 단계 추가
5. [x] 라우터에서 전용 `TextGenerationPort`(gpt-5-mini) 주입
6. [x] 단위 테스트

**관련**
- [BL-BE-24](BL-BE-24-stock-theme-recommendation.md) — 키워드·테마 매칭 추천
- [BL-BE-50](BL-BE-50-llm-responses-infrastructure.md) — Responses Port·클라이언트

**개정 이력**
- 2026-03-30: 초안 및 구현
- 2026-03-30: `GET /stock-theme/recommend` — `user_token` 쿠키 + DB 댓글 기반 명사 빈도로 추천(본문 없이 호출)
