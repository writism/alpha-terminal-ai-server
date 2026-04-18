# BL-BE-75

**Backlog Type**
UseCase Backlog

**Backlog Title**
시스템이 투자 판단 요청을 수신하면 1시간 이내 동일 종목의 캐시된 결과를 즉시 반환한다

**배경**
현재 동일 종목을 반복 분석할 때마다 LLM 파이프라인이 처음부터 재실행된다.
analysis_cache 테이블에 결과를 저장하고, TTL 이내 요청은 캐시에서 반환한다.

**Success Criteria**
- 동일 종목의 분석 결과가 DB에 저장된다
- 1시간 이내 동일 종목 재요청 시 저장된 결과가 즉시 반환된다
- 캐시 히트 응답에 `cached: true`, `cached_at` 필드가 포함된다
- 사용자가 강제 재분석 요청(`force: true`) 시 캐시를 무시하고 파이프라인을 재실행한다
- 캐시 만료(1시간 초과) 시 파이프라인을 재실행하고 결과를 갱신한다

**Todo**
1. `analysis_cache` 테이블 ORM 모델과 Repository를 구현한다
2. 캐시 조회 UseCase를 구현한다 (symbol + expires_at 조건)
3. 파이프라인 실행 완료 후 결과를 캐시에 저장하는 로직을 추가한다
4. 투자 판단 Router에 `force` 파라미터를 추가하고 캐시 히트 응답 형식을 정의한다
5. 캐시 히트 시 즉시 반환, 미스 시 파이프라인 실행 후 저장하는 흐름을 완성한다
