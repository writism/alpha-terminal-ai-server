# BL-BE-55

**Backlog Type**
Feature / market_analysis + LangChain Tool

**Backlog Title**
market_analysis 체인에 get_user_profile LangChain Tool 추가

**Success Criteria**
- `market_analysis` 도메인의 LangChain 체인에 `get_user_profile` Tool이 추가된다.
- Tool은 인증된 사용자의 `user_profile`을 DB에서 조회하여 LangChain Agent에 컨텍스트로 제공한다.
- AI는 분석 요청 시 사용자 프로필을 먼저 조회한 뒤 분석을 수행한다.
- `user_token` 쿠키로 인증된 사용자만 사용 가능하다.
- 투자 추천은 생성하지 않는다.

**Todo**
1. [ ] `user_profile` 도메인의 Repository Port를 정의한다
2. [ ] `get_user_profile` LangChain Tool을 구현한다 (`@tool` 데코레이터 또는 `BaseTool` 상속)
3. [ ] `UserProfileRepositoryImpl` — DB에서 user_profile 조회 구현
4. [ ] 기존 `market_analysis` LangChain 체인에 Tool을 바인딩한다
5. [ ] Tool 호출 결과가 프롬프트 컨텍스트에 반영되는지 테스트한다

**관련**
- [BL-BE-52](BL-BE-52-market-analysis-langchain-qa.md) — market_analysis LangChain 기반 체인
- [BL-BE-56](BL-BE-56-personalized-prompt.md) — 사용자 취향 기반 맞춤 프롬프트

**개정 이력**
- 2026-04-11: 초안
