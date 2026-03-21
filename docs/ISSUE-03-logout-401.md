# ISSUE-03: POST /auth/logout 401 Unauthorized

작성일: 2026-03-21

---

## 현상

Navbar 로그아웃 버튼 클릭 시 401 오류 발생.

```
POST http://localhost:33333/auth/logout 401 (Unauthorized)
```

백엔드 세션이 서버에서 무효화되지 않아 보안상 문제가 있었다.
프론트는 try/catch/finally로 처리하고 있어 UX에는 영향 없었음.

---

## 원인

### 인증 시스템 이중화 문제

백엔드에 두 가지 독립적인 인증 시스템이 혼재하고 있었다.

| 시스템 | 엔드포인트 | 인증 방식 | 용도 |
|--------|-----------|-----------|------|
| `auth` 도메인 | `POST /auth/logout` | `Authorization: Bearer <token>` 헤더 | 기존 admin 로그인 전용 |
| `account` 도메인 | (없었음) | `session_token` Cookie | 카카오 로그인 / 신규 회원가입 |

카카오 로그인 및 신규 회원가입 완료 후 발급되는 세션 토큰은 `session_token` 쿠키(HttpOnly)로 저장된다. 그러나 `/auth/logout`은 `Authorization: Bearer` 헤더만 인식하므로 쿠키를 보내도 항상 401을 반환한다.

### 세션 저장소도 분리됨

```
RedisSessionAdapter       ← auth 도메인 (Authorization: Bearer 전용)
RedisAccountSessionAdapter ← account 도메인 (Cookie 기반, session: prefix)
```

두 어댑터가 서로 다른 Redis 키 구조를 사용하므로 `/auth/logout`이 쿠키 토큰으로 조회해도 세션을 찾을 수 없다.

---

## 수정 내용

### 신규 엔드포인트: `POST /account/logout`

카카오 로그인/회원가입 세션을 처리하는 `account` 도메인에 전용 로그아웃 엔드포인트를 추가했다.

#### 추가/변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `account/application/usecase/account_session_port.py` | `delete(session_token)` 추상 메서드 추가 |
| `account/adapter/outbound/in_memory/redis_account_session_adapter.py` | `delete()` 구현 — Redis `session:{token}` 키 삭제 |
| `account/application/usecase/logout_account_usecase.py` | 신규 생성 |
| `account/adapter/inbound/api/account_router.py` | `POST /account/logout` 엔드포인트 추가 |

#### 엔드포인트 스펙

```
POST /account/logout
Cookie: session_token=xxxx  또는  user_token=xxxx
credentials: include
```

**성공 응답:**
```
HTTP 200 OK
Set-Cookie: session_token=; Max-Age=0   ← 쿠키 삭제
Set-Cookie: user_token=; Max-Age=0
Set-Cookie: nickname=; Max-Age=0
Set-Cookie: email=; Max-Age=0
Set-Cookie: account_id=; Max-Age=0

{
  "message": "로그아웃 되었습니다."
}
```

**실패 응답:**
```
HTTP 401 Unauthorized
{ "detail": "로그인 상태가 아닙니다." }
```

#### 동작 흐름

```
1. 쿠키에서 session_token 또는 user_token 추출
2. Redis에서 session:{token} 키 삭제 (서버 세션 무효화)
3. 응답에서 모든 인증 관련 쿠키 삭제
   - session_token, user_token, nickname, email, account_id
4. 200 OK 반환
```

---

## 프론트엔드 수정 요청

### 로그아웃 호출 경로 변경

```typescript
// 변경 전 (401 발생)
POST http://localhost:33333/auth/logout

// 변경 후
POST http://localhost:33333/account/logout
```

### 수정 코드 예시

```typescript
const logoutUser = async () => {
  try {
    await fetch('http://localhost:33333/account/logout', {
      method: 'POST',
      credentials: 'include',  // ← session_token 쿠키 자동 전송
    })
  } catch (e) {
    // 네트워크 오류 무시
  } finally {
    // 프론트 상태 초기화 (기존 로직 유지)
    clearLocalAuthState()
    router.replace('/login')
  }
}
```

> `credentials: 'include'` 필수. 이 옵션이 없으면 쿠키가 전송되지 않아 401 발생.

### 기존 `/auth/logout` 사용 여부

`/auth/logout`은 `Authorization: Bearer` 헤더 기반의 별도 어드민 로그인 전용이므로 카카오/일반 회원 로그아웃에는 사용하지 않는다.

---

## 현재 상태

| 항목 | 상태 |
|------|------|
| 원인 분석 | ✅ 완료 |
| `POST /account/logout` 구현 | ✅ 완료 |
| 프론트 로그아웃 URL 변경 | **미완료 — 프론트 팀 적용 필요** |
