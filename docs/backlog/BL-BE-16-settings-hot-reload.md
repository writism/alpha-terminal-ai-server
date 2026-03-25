# BL-BE-16

**Backlog Type**  
Config / DevEx

**Backlog Title**  
`get_settings()` — `.env` 변경을 요청 단위에서 반영 (lru 캐시 제거)

---

## 1. 배경

- `get_settings`에 `@lru_cache`가 있으면 **프로세스 재시작 전**까지 `Settings`가 고정되어, API 키만 `.env`에서 고친 경우에도 라우터가 매 요청 `get_settings()`를 호출해도 갱신되지 않았다.

## 2. 목표

| ID | 기준 |
|----|------|
| SC-1 | `get_settings()` 호출마다 **새 `Settings()` 인스턴스**가 생성되어 pydantic이 env/`.env`를 다시 읽는다. |
| SC-2 | **모듈 import 시 한 번만** 잡히는 값(`redis_client`의 연결 파라미터, `main.py`의 `settings` 상수 등)은 여전히 **프로세스 시작 시점** 기준임을 문서에 명시한다. |

## 3. 비범위

- Redis/MySQL 연결을 런타임에 끊고 재연결하는 **풀 핫 스왑**은 포함하지 않는다(재시작 필요).

## 4. 관련 백로그

- **BL-BE-15**: 히트맵 Redis 캐시는 `get_settings()`로 플래그 갱신 가능.

## 5. 완료 정의

- [x] `settings.py`에서 `@lru_cache` 제거.
- [x] 본 문서에 import 시점 캐시 제약 명시.
