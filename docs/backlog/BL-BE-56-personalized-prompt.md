# BL-BE-56

**Backlog Type**
Feature / market_analysis + LangChain

**Backlog Title**
사용자 취향 기반 맞춤 프롬프트 개선

**Success Criteria**
- AI 분석 프롬프트에 사용자 프로필(관심 섹터, 투자 성향, 선호 분석 스타일 등)이 반영된다.
- 동일한 종목이라도 사용자별로 다른 관점의 분석 결과가 생성된다.
- 프롬프트 템플릿은 `user_profile` 필드를 동적으로 주입하는 구조로 구성한다.
- 투자 추천 문구는 포함하지 않는다.

**Todo**
1. [ ] 현재 `market_analysis` 프롬프트 템플릿을 분석하여 개인화 주입 포인트를 파악한다
2. [ ] 사용자 프로필 필드(관심 섹터, 투자 성향 등)를 프롬프트 변수로 추가한다
3. [ ] `PromptTemplate` 또는 `ChatPromptTemplate`에 user_profile 컨텍스트 블록을 삽입한다
4. [ ] 프로필 없는 사용자(신규)는 기본 프롬프트로 fallback 처리한다
5. [ ] 프로필 유무에 따른 분석 결과 차이를 테스트한다

**관련**
- [BL-BE-55](BL-BE-55-user-profile-tool-langchain.md) — get_user_profile Tool
- [BL-BE-57](BL-BE-57-personalized-tag-ui.md) — 분석 카드 개인화 태그 FE

**개정 이력**
- 2026-04-11: 초안
