# 토큰 기반 사용자 식별을 위한 Redis 세션 저장소 구축

작성자: 이승욱
작성일: 2026-03-18
관련 백로그: ADAIS-25

---

## Backlog Title

시스템이 토큰 기반 사용자 식별을 위한 Redis 세션 저장소를 구축한다

---

## Success Criteria

- 사용자가 로그인에 성공하면 시스템이 세션 토큰을 생성하고 Redis에 저장한다
- 세션 데이터에는 사용자 식별 정보(사용자 ID, 역할 등)가 포함된다
- 해킹을 방지하기 위해 인증 비밀번호가 존재한다
- 토큰을 키로 Redis에서 세션 정보를 조회할 수 있다
- 세션에는 만료 시간(TTL)이 설정되어 일정 시간 후 자동으로 삭제된다
- 유효하지 않거나 만료된 토큰으로 조회 시 세션 정보가 반환되지 않는다

---

## Todo

- [x] Redis 연결 설정 및 클라이언트를 Infrastructure에 구성한다
- [x] 세션 토큰 생성 및 저장 기능을 구현한다
- [x] 토큰 기반 세션 조회 기능을 구현한다
- [x] 세션 만료(TTL) 정책을 적용한다
- [x] 세션 삭제(로그아웃) 기능을 구현한다

---

## 구현 위치 (예정)

| 레이어 | 파일 |
|--------|------|
| Infrastructure | `app/infrastructure/cache/redis_client.py` |
| Infrastructure Config | `app/infrastructure/config/settings.py` (REDIS_HOST, REDIS_PORT 추가) |
| Domain Entity | `app/domains/auth/domain/entity/session.py` |
| Application Port | `app/domains/auth/application/usecase/session_repository_port.py` |
| Application UseCase | `app/domains/auth/application/usecase/create_session_usecase.py` |
| Application UseCase | `app/domains/auth/application/usecase/get_session_usecase.py` |
| Application UseCase | `app/domains/auth/application/usecase/delete_session_usecase.py` |
| Outbound Adapter | `app/domains/auth/adapter/outbound/persistence/redis_session_repository.py` |
| Inbound Adapter | `app/domains/auth/adapter/inbound/api/auth_router.py` |

## 주요 설계 결정

- 세션 토큰: `secrets.token_urlsafe(32)` 생성
- TTL: 기본 3600초 (1시간)
- Redis key 형식: `session:{token}`
- 세션 데이터: `{"user_id": ..., "role": ..., "created_at": ...}`
- 인증 비밀번호: `.env`의 `AUTH_SECRET` 환경변수로 관리

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-18 | 이승욱 | 최초 작성 |
