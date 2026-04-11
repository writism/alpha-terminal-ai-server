# BL-BE-57

**Backlog Type**
Feature / Frontend + market_analysis

**Backlog Title**
분석 결과 카드에 개인화 태그 표시

**Success Criteria**
- AI 분석 결과 카드에 "이 분석은 회원님의 관심 종목 기준으로 맞춤화되었습니다" 형태의 개인화 태그가 표시된다.
- 태그는 백엔드 응답에 `is_personalized: bool` 필드가 포함된 경우에만 렌더링된다.
- 비로그인 또는 프로필 미설정 사용자에게는 태그가 표시되지 않는다.
- 기존 분석 카드 컴포넌트를 수정하며, 새 컴포넌트를 추가하지 않는다.

**Todo**
1. [ ] BE `market_analysis` 응답 DTO에 `is_personalized: bool` 필드를 추가한다
2. [ ] FE 분석 결과 카드 컴포넌트에서 `is_personalized` 값을 읽어 태그를 조건부 렌더링한다
3. [ ] 태그 스타일을 기존 Alpha-Desk 테마(다크/라이트)에 맞게 적용한다
4. [ ] 비로그인/프로필 없음 상태에서 태그가 노출되지 않는지 확인한다

**관련**
- [BL-BE-56](BL-BE-56-personalized-prompt.md) — 맞춤 프롬프트
- [BL-BE-55](BL-BE-55-user-profile-tool-langchain.md) — get_user_profile Tool

**개정 이력**
- 2026-04-11: 초안
