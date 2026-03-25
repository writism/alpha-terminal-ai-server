# BL-BE-09

**Backlog Type**
Bug Fix Backlog

**Backlog Title**
시스템이 카카오 로그인 시 기존 사용자를 kakao_id로 정확히 식별한다

**Status**
완료 (2026-03-23)

**배경 / 버그 설명**
이미 가입된 사용자가 카카오로 로그인해도 약관 페이지(→ 회원가입 페이지)로 이동하고,
회원가입 시 "카카오 로그인 세션이 만료되었습니다" 에러가 발생한다.

재현 시나리오:
1. btdlm 계정으로 카카오 로그인 (이미 가입된 사용자)
2. /auth-callback 에서 약관 페이지로 리다이렉트 (버그)
3. 약관 동의 → /account/signup 에서 "카카오 로그인 세션이 만료" 에러 발생

**Root Cause**
`CheckKakaoUserRegistrationUseCase.execute()`에서 기존 사용자 조회를 `find_by_email(user.email)`로만 수행한다.
카카오 계정의 이메일 제공이 선택 사항이므로 이메일이 없는 경우 빈 문자열로 조회하게 되고,
이 경우 기존 사용자를 찾지 못해 신규 사용자 흐름(temp_token 발급)으로 처리된다.

accounts 테이블에 kakao_id 컬럼이 존재하나 조회에 활용되지 않았음.

**Success Criteria**
- 카카오 로그인 시 kakao_id로 기존 계정을 조회하여 기존 사용자를 정확히 식별한다
- 이메일 제공 여부와 관계없이 기존 사용자는 로그인 후 대시보드로 이동한다
- 신규 사용자는 기존대로 약관 페이지로 이동한다

**Todo**
1. [x] AccountRepositoryPort에 find_by_kakao_id() 추가
2. [x] AccountRepositoryImpl에 find_by_kakao_id() 구현
3. [x] CheckKakaoUserRegistrationUseCase에서 kakao_id로 먼저 조회하도록 수정

**변경된 파일**
- `app/domains/account/application/usecase/account_repository_port.py`
- `app/domains/account/adapter/outbound/persistence/account_repository_impl.py`
- `app/domains/kakao_auth/application/usecase/check_kakao_user_registration_usecase.py`
