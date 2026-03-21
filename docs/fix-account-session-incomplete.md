# Fix: account 도메인 미완성 코드 수정

## 발생일
2026-03-21

## 배경

이전 세션에서 ISSUE-02, ISSUE-03, BE-02, BE-05, BE-07을 반영하기 위해
`logout_account_usecase.py`, `account_session_port.py` 신규 파일을 생성했으나,
의존하는 기존 파일들이 미완성 상태로 남아 런타임 오류가 발생할 수 있었다.

---

## 발견된 문제

### 문제 1: `redis_account_session_adapter.py` — 메서드 누락

`kakao_authentication_router.py`에서 다음 메서드를 호출하지만 어댑터에 정의되지 않음:

| 호출 위치 | 호출 메서드 | 실제 존재 여부 |
|-----------|-------------|----------------|
| `kakao_authentication_router.py:69` | `.create(account_id)` | ❌ 없음 (`.create_session()`만 존재) |
| `kakao_authentication_router.py:70` | `.save_account_kakao_token(account_id, token)` | ❌ 없음 |
| `logout_account_usecase.py:9` | `.delete(session_token)` | ❌ 없음 |

**영향**: 기존 회원 카카오 로그인 시 `AttributeError` 런타임 오류 발생.

### 문제 2: `account_router.py` — ISSUE-02/03/BE-02/BE-05 미적용

| 항목 | 내용 | 적용 여부 |
|------|------|-----------|
| ISSUE-02 | `/register` 응답을 302 Redirect → 200 JSONResponse로 변경 | ❌ 미적용 |
| ISSUE-03 | `POST /account/logout` 엔드포인트 추가 | ❌ 미적용 |
| BE-02 | 회원가입 완료 후 `account_id` 쿠키 발급 | ❌ 미적용 |
| BE-05 | Exception 메시지 노출 방지 (`detail=str(e)` → 내부 오류 메시지) | ❌ 미적용 |

### 문제 3: `register_account_usecase.py` — print() 미제거

- `print(f"[Register] ...")` 문장이 남아 있어 BE-07 미적용 상태.

---

## 수정 내용

### Fix 1: `redis_account_session_adapter.py`

추가된 메서드:

```python
def create(self, account_id: int) -> str:
    # kakao_authentication_router에서 호출 — create_session()과 동일 로직
    token = str(uuid.uuid4())
    session = Session(token=token, user_id=str(account_id), role=UserRole.USER, ttl_seconds=SESSION_TTL_SECONDS)
    self._session_adapter.save(session)
    return token

def save_account_kakao_token(self, account_id: int, kakao_access_token: str) -> None:
    # account_id 기반 Kakao 액세스 토큰을 Redis에 저장
    key = KAKAO_TOKEN_KEY_PREFIX + str(account_id)
    self._redis.setex(key, KAKAO_TOKEN_TTL_SECONDS, kakao_access_token)

def delete(self, session_token: str) -> None:
    # 로그아웃 시 세션 삭제
    self._session_adapter.delete(session_token)
```

Redis 키 규칙:
- 세션: `session:{token}` (RedisSessionAdapter 위임)
- Kakao 토큰: `kakao_token:{account_id}` (RedisKakaoTokenAdapter와 동일 규칙)

### Fix 2: `account_router.py`

변경 사항:

- **ISSUE-02**: `RedirectResponse(302)` → `JSONResponse({"success": True, "redirect_url": ...})`
  - fetch() + cross-origin 302 redirect는 CORS 정책에 의해 자동 follow 불가
  - 프론트엔드에서 `window.location.href`로 리다이렉트 처리
- **BE-02**: `account_id` 쿠키 추가 (`max_age=7일`)
- **ISSUE-03**: `POST /account/logout` 엔드포인트 추가
  - `session_token` 또는 `user_token` 쿠키에서 토큰 수신
  - `LogoutAccountUseCase` 실행 → Redis 세션 삭제
  - 모든 쿠키 (`session_token`, `user_token`, `nickname`, `email`, `account_id`) 삭제
- **BE-05**: `except Exception as e: detail=str(e)` → `logger.exception()` + 고정 메시지 반환

### Fix 3: `register_account_usecase.py`

- `print(...)` → `logger.debug(...)` (BE-07)

---

## 수정 파일 목록

| 파일 | 변경 유형 |
|------|-----------|
| `app/domains/account/adapter/outbound/in_memory/redis_account_session_adapter.py` | 수정 |
| `app/domains/account/adapter/inbound/api/account_router.py` | 수정 |
| `app/domains/account/application/usecase/register_account_usecase.py` | 수정 |

---

## 관련 이슈

- ISSUE-02: POST /account/register CORS 리다이렉트 문제
- ISSUE-03: POST /auth/logout 401 Unauthorized
- BE-02: account_id 쿠키 누락
- BE-05: Exception 메시지 노출
- BE-07: print() 제거
