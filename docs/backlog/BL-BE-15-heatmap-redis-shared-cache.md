# BL-BE-15

**Backlog Type**  
API / Infra / Cost-control

**Backlog Title**  
일별 등락 히트맵 upstream 결과 — Redis 공유 캐시 (워커 간·재시작 후 TTL 내 재사용)

---

## 1. 배경

- BL-BE-13/14의 인메모리 캐시는 **프로세스 로컬**이라 uvicorn worker가 여러 개이거나 재시작 시 캐시가 비어 upstream 호출이 다시 늘어난다.
- 앱은 이미 `redis`·`app/infrastructure/cache/redis_client.py`로 세션 등에 Redis를 쓰고 있다.

## 2. 목표 (Success Criteria)

| ID | 기준 |
|----|------|
| SC-1 | 동일 `(provider, symbol, weeks, end_day_bucket)` 에 대해 **Redis에 일봉 close 시퀀스**가 TTL 동안 저장된다. |
| SC-2 | Redis 히트 시 **외부 API를 다시 호출하지 않는다**(인메모리 미스여도). |
| SC-3 | Redis 장애·미연결 시 **기존과 같이 동작**(인메모리 + 직접 upstream, 예외 삼키고 로그만 debug). |
| SC-4 | 키 네임스페이스 접두사로 **다른 Redis 키와 충돌하지 않는다**. |

## 3. 설계

- 키: `alphadesk:heatmap:closes:v1:{provider}:{symbol}:{weeks}:{end_date}` (`|` 대신 `:` 사용).
- 값: JSON `[[ "2025-01-02", 71200.0 ], ...]`.
- TTL: 1800초(BL-BE-13 인메모리 TTL과 동일).
- 조회 순서: 인메모리 → Redis → upstream; 저장: upstream 성공 시 인메모리 + Redis.

## 4. 설정

- `heatmap_redis_cache_enabled` (기본 `true`): `false`면 Redis 읽기/쓰기 생략(로컬 디버그용).

## 5. 관련 백로그

- **BL-BE-13** §9, **BL-BE-14**, **BL-BE-16**(설정 리로드와 Redis 호스트 변경은 별도 제약).

## 6. 완료 정의

- [x] `heatmap_redis_cache` 모듈 + use case 연동.
- [x] `.env.example`에 플래그 문서화.
- [x] Redis 불가 시에도 API 200·부분 실패 계약 유지.
