# ISSUE-02: 회원가입 후 CORS 오류로 리다이렉트 실패

작성일: 2026-03-21

---

## 현상

`/signup` 페이지에서 가입하기 버튼 클릭 시 "서버 오류가 발생했습니다." 메시지가 표시되고 메인 페이지로 이동하지 않는다.

콘솔 오류:

```
Access to fetch at 'http://localhost:3000/signup?nickname=...'
(redirected from 'http://localhost:33333/account/register')
from origin 'http://localhost:3000' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

---

## 원인

### fetch() + credentials: include + cross-origin 302 리다이렉트 조합 문제

프론트가 `fetch()`로 `POST /account/register`를 호출하고 백엔드가 `302 → http://localhost:3000`으로 응답하면 다음 흐름이 발생한다.

```
[프론트 fetch]
  localhost:3000 → POST http://localhost:33333/account/register
                          ↓
                   302 Location: http://localhost:3000
                          ↓
  fetch()가 자동으로 redirect 추적
                          ↓
  GET http://localhost:3000  ← 새 cross-origin 요청 발생
                          ↓
  localhost:3000는 CORS 헤더 없음 (Next.js 페이지)
                          ↓
  ❌ CORS blocked
```

`fetch()` API는 `credentials: include` 옵션과 함께 cross-origin 302 리다이렉트를 따라갈 때, 리다이렉트 대상 URL에도 CORS 헤더가 필요하다. `localhost:3000`은 Next.js 프론트엔드이므로 CORS 헤더를 반환하지 않아 차단된다.

### 왜 카카오 로그인 redirect는 문제없나?

카카오 로그인 리다이렉트는 `fetch()`가 아닌 `window.location.href`로 브라우저가 직접 이동하기 때문에 CORS 정책 적용 대상이 아니다.

```
[카카오 로그인 — 정상 동작]
  window.location.href = 'http://localhost:33333/kakao-authentication/request-oauth-link'
  → 브라우저 직접 이동 → CORS 적용 안 됨
```

---

## 해결 방법

### 백엔드 변경 (완료)

`302 RedirectResponse` 대신 `200 JSONResponse`로 변경. 쿠키는 동일하게 `Set-Cookie`로 세팅. 리다이렉트 URL을 응답 바디에 포함.

**`account/adapter/inbound/api/account_router.py`**

```python
# 변경 전
response = RedirectResponse(url=frontend_url, status_code=302)

# 변경 후
response = JSONResponse(content={"success": True, "redirect_url": frontend_url})
```

응답 예시:

```
HTTP 200 OK
Set-Cookie: session_token=...; HttpOnly; SameSite=Lax
Set-Cookie: nickname=su; SameSite=Lax
Set-Cookie: email=lubh@hanmail.net; SameSite=Lax
Set-Cookie: account_id=1; SameSite=Lax

{
  "success": true,
  "redirect_url": "http://localhost:3000"
}
```

### 프론트엔드 변경 필요

응답을 받으면 `window.location.href`로 직접 이동해야 한다.

```typescript
const handleRegister = async () => {
  const res = await fetch('http://localhost:33333/account/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',   // ← 쿠키 전달/수신에 필수
    body: JSON.stringify({ nickname, email }),
  })

  if (!res.ok) {
    // 에러 처리
    return
  }

  const data = await res.json()
  if (data.success) {
    window.location.href = data.redirect_url  // ← fetch 대신 브라우저 직접 이동
  }
}
```

> `window.location.href`는 브라우저 탐색이므로 CORS 적용 대상이 아니다.
> 또한 이 시점에 `Set-Cookie`로 세팅된 쿠키가 브라우저에 저장되어 있으므로, 이동 후 메인 페이지에서 `nickname`, `email`, `account_id` 쿠키를 정상적으로 읽을 수 있다.

---

## fetch() vs window.location.href 기준

| 방식 | 사용 시점 | CORS 적용 |
|------|-----------|-----------|
| `fetch()` | API 데이터 요청/응답이 필요한 경우 | ✅ 적용됨 |
| `window.location.href` | 브라우저 페이지 이동이 목적인 경우 | ❌ 적용 안 됨 |

인증 관련 최종 리다이렉트(로그인 완료 후 메인 이동, 회원가입 완료 후 메인 이동)는 항상 `window.location.href`를 사용한다.

---

## 현재 상태

| 항목 | 상태 |
|------|------|
| 백엔드 `302` → `200 JSON` 변경 | ✅ 완료 |
| 프론트 `window.location.href` 처리 | **미완료 — 프론트 팀 적용 필요** |
