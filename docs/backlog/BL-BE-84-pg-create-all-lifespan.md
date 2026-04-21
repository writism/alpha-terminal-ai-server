# BL-BE-84: PG create_all 모듈 레벨 → lifespan 이동

## 문제

`main.py` 모듈 최상단에서 `PgBase.metadata.create_all(bind=pg_engine)` 가 실행된다.

- import 타임(앱 로드 시점)에 DB 연결을 시도하여 서버 기동 실패 가능성
- Alembic 기반 관리와 병행 시 "이미 존재하는 테이블" 충돌 위험
- 개발 환경과 운영 환경의 스키마 드리프트(인덱스·default·FK 차이) 누적

## 해결 방안

`PgBase.metadata.create_all()` 호출을 `lifespan` startup 섹션으로 이동.
동작은 기존과 동일(앱 기동 시 1회 실행)하지만 lifecycle 이 명확해진다.
향후 PG Alembic cutover 시 이 줄만 제거하면 된다.

## 범위

- `main.py`

## 완료 기준

- 모듈 레벨 `create_all` 호출 제거
- `lifespan` startup 에 이동, TODO 주석으로 Alembic cutover 전제 명시
