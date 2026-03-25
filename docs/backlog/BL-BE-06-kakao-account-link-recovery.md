# BL-BE-06

**Backlog Type**
Behavior Backlog

**Backlog Title**
시스템이 기존 등록 사용자의 Kakao 계정 연결 정보를 정확히 복구한다

**배경 / 원인**
일부 계정은 회원가입 시 실제 Kakao 사용자 식별자(`kakao_id`)가 아니라
사용자 입력 이메일 값이 `accounts.kakao_id`에 저장되었다.
이 경우 이후 카카오 로그인 시 `/request-access-token-after-redirection` 경로에서
실제 `kakao_id`로 계정을 찾지 못하고 신규 사용자로 오인하여 약관/회원가입 화면으로 이동한다.
특히 카카오 측 이메일 제공값이 비어 있으면 email fallback 조회도 실패하여
이미 등록된 사용자도 계속 회원가입 흐름에 머무르게 된다.

**Success Criteria**
- 회원가입 시 `accounts.kakao_id`에는 실제 Kakao 사용자 식별자가 저장된다
- 카카오 로그인 시 `kakao_id`로 기존 계정을 정확히 조회한다
- 과거에 `kakao_id=email` 형태로 잘못 저장된 계정은 재회원가입 시도 시 자동 복구된다
- 복구된 계정은 새 계정을 중복 생성하지 않고 세션만 발급받는다
- 이후 동일 사용자의 카카오 재로그인 시 약관 화면이 아니라 기존 사용자 흐름으로 진입한다

**Todo**
1. 가입용 temp token에서 `kakao_access_token`과 `kakao_id`를 함께 읽을 수 있도록 account 도메인 포트를 수정한다
2. 회원가입 시 실제 `kakao_id`를 `accounts.kakao_id`에 저장하도록 수정한다
3. `kakao_id=email` 형태의 레거시 계정을 감지해 현재 `kakao_id`로 자동 복구하는 로직을 추가한다
4. 자동 복구된 계정은 신규 row 생성 없이 세션 발급 및 카카오 토큰 저장만 수행하도록 수정한다
