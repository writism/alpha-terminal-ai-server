# BL-BE-54: 시스템이 비정형 데이터 수집을 위한 환경을 구성한다

## Summary

Alpha Desk 비정형 데이터(뉴스 원문, 공시 본문, 리포트 등) 저장을 위해
PostgreSQL + JSONB 기반 인프라를 구성한다.
기존 MySQL은 정형 데이터(계정, 관심종목 등)에 유지하고,
비정형 수집 데이터는 PostgreSQL JSONB로 분리 저장한다.

## Success Criteria

- **이 작업은 PostgreSQL를 기반으로 동작한다.**
- 애플리케이션 실행 시 PostgreSQL 데이터베이스에 대한 연결 설정이 환경 변수로부터 로드된다
- 입력 정보는 데이터베이스 호스트, 포트, 사용자, 비밀번호, 데이터베이스 이름을 포함한다
- 시스템은 PostgreSQL 연결 풀을 초기화하고 헬스 체크를 수행한다
- 비정형 데이터를 저장할 수 있도록 JSONB 컬럼 타입을 지원하는 스키마가 준비된다
- 연결이 성공하면 애플리케이션이 정상 기동되고, 실패 시 명확한 에러 로그가 출력된다

## To-do

- [x] PostgreSQL 연결 환경 변수 스키마를 정의하고 로드하는 설정을 구성한다
- [x] PostgreSQL 데이터베이스 세션 및 연결 풀 초기화 기능을 구성한다
- [x] 비정형 데이터 저장을 위한 JSONB 기반 ORM 모델 베이스를 구성한다
- [x] 애플리케이션 기동 시점에 데이터베이스 연결 헬스 체크를 수행한다
- [x] 데이터베이스 마이그레이션 도구(Alembic) 초기 환경을 구성한다

## 구현 위치

- `app/infrastructure/config/settings.py` — PG 환경 변수 추가
- `app/infrastructure/database/pg_session.py` — PG 엔진, 세션, PgBase
- `alembic.ini`, `alembic/` — 마이그레이션 환경
- `main.py` — lifespan에 PG 헬스 체크 추가
- `requirements.txt` — psycopg2-binary, alembic 추가
