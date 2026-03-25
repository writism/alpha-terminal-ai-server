# BL-BE-04

**Backlog Type**
Behavior Backlog

**Backlog Title**
API 서버가 관심종목 심볼에 대해 정확한 뉴스 기사를 수집한다

**배경 / 원인**
`NewsCollectorAdapter`의 `SYMBOL_TO_NAME` 딕셔너리에 등록되지 않은 심볼(예: 060250)은
`SYMBOL_TO_NAME.get(symbol, symbol)` 호출 시 종목 코드 숫자 그대로 검색 키워드로 사용된다.
SerpAPI에 "060250"이라는 숫자를 검색하면 해당 종목과 무관한 기사(예: 한화)가 반환되고,
AI가 이를 요약하여 대시보드에 엉뚱한 종목 요약이 표시된다.

재현 확인:
- 관심종목 060250(NHN KCP) 파이프라인 실행
- 대시보드 AI 요약에 "한화" 관련 내용과 태그 표시
- `SYMBOL_TO_NAME`에 `"060250"` 키 없음

**Success Criteria**
- `SYMBOL_TO_NAME`에 등록된 심볼은 해당 한글 회사명으로 SerpAPI 검색을 수행한다
- 종목 코드 숫자를 그대로 검색 키워드로 사용하지 않는다
- 060250 수집 시 NHN KCP 관련 뉴스 기사를 반환한다
- 매핑이 없는 심볼로 수집 시도 시 경고 로그를 출력한다

**Todo**
1. `SYMBOL_TO_NAME`에 `"060250": "NHN KCP"` 매핑을 추가한다
2. `SYMBOL_TO_ENGLISH`에 `"060250": "NHN KCP"` 매핑을 추가한다
3. `collect()` 메서드에서 심볼이 `SYMBOL_TO_NAME`에 없을 때 경고 로그를 출력하도록 구현한다
