# BL-BE-05

**Backlog Type**
Behavior Backlog

**Backlog Title**
시스템이 임시 토큰으로 임시 사용자 정보를 조회한다

**배경**
기존 /authentication/me 엔드포인트는 isTemporary(bool) 필드를 반환했으나,
프론트엔드가 is_registered(bool) 필드로 신규/기존 사용자를 판정해야 한다.
temp_token 외 user_token 형태로 올 수도 있으며 두 경우 모두 일관성 있게 처리해야 한다.
검증을 위해 토큰, nickname, email 정보를 print로 출력한다.

**대상 도메인**
순수 Authentication 도메인 (app/domains/auth/)
기존 /authentication/me 엔드포인트를 수정한다.

**Success Criteria**
- GET /authentication/me 요청 시 temp_token 또는 user_token 쿠키를 검사한다
- user_token이 유효한 경우 is_registered: true 와 nickname, email, account_id를 반환한다
- temp_token이 Redis에 존재하는 경우 is_registered: false 와 nickname, email을 반환한다
- 유효한 토큰이 없으면 401 에러를 반환한다
- 기대 응답: {"is_registered": false, "nickname": "...", "email": "..."}
- 토큰, nickname, email 정보를 print로 출력하여 동작 검증을 지원한다

**Todo**
1. MeResponse의 isTemporary 필드를 is_registered 필드로 교체한다
2. GetMeUseCase의 반환 로직을 is_registered 기준으로 수정한다
3. user_token 세션 조회 시 account_id를 응답에 포함하도록 구현한다
4. 토큰, nickname, email을 print로 출력하는 디버그 로그를 구현한다
