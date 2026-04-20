# MySQL Migration Inventory & Baseline Plan

> 작성일: 2026-04-18
> 대상 저장소: `alpha-terminal-ai-server`
> 목적: 현재 스키마 관리 경로를 inventory 하고, MySQL 기준 versioned migration baseline 전환 절차를 확정한다.

---

## 1. 결론 요약

현재 백엔드의 DB 스키마 관리는 **완전히 migration 기반으로 전환된 상태가 아니다.**

실제 상태는 다음과 같다.

- **MySQL**
  - `Base.metadata.create_all()` 로 테이블 생성
  - `main.py` 내부 `_run_column_migrations()` 로 누락 컬럼/인덱스 수동 보정
- **PostgreSQL**
  - `PgBase.metadata.create_all()` 사용
  - `alembic/env.py` 는 `PgBase.metadata` 를 바라봄
  - 하지만 `alembic/versions/` 는 비어 있음

즉, 현재는:

- 문서에는 Alembic 기반 운영 의도가 존재하지만
- 실제 런타임은 여전히 `create_all + 수동 SQL` 중심이고
- 실제 Alembic 이력 파일은 비어 있다

따라서 지금 필요한 것은 "새 migration 하나 추가"가 아니라,
**MySQL 기준 baseline 확립 + 기존 DB stamp 전략 + runtime schema 변경 제거 계획**이다.

---

## 2. 현재 스키마 관리 경로 inventory

## 2-1. 런타임 초기화

### MySQL

파일:
- `main.py`
- `app/infrastructure/database/session.py`

현재 동작:

1. `session.py` 에서 MySQL `Base`와 `engine` 생성
2. `main.py` 시작 시 `Base.metadata.create_all(bind=engine)` 실행
3. 이어서 `_run_column_migrations()` 실행

이 방식의 의미:

- 없는 테이블은 자동 생성 가능
- 기존 테이블 변경은 ORM만으로 반영되지 않으므로 수동 SQL 보정이 계속 누적됨

### PostgreSQL

파일:
- `main.py`
- `app/infrastructure/database/pg_session.py`
- `alembic/env.py`

현재 동작:

1. `PgBase.metadata.create_all(bind=pg_engine)` 실행
2. `alembic/env.py` 는 `PgBase.metadata` 를 대상으로 설정됨
3. 그러나 실제 `alembic/versions/` 파일은 없음

즉, PostgreSQL도 "Alebmic 준비는 되어 있으나 실운영 revision 이력은 없음" 상태다.

---

## 2-2. MySQL 수동 컬럼/인덱스 보정 목록

2026-04-18 로컬 전용 정리 기준 현재 `main.py` 에는 `_run_column_migrations()` 가 없다.

제거 직전 호환 레이어가 처리하던 항목은 아래 6개였다.

| 순번 | 테이블 | 변경 내용 | 목적/배경 |
|------|--------|-----------|-----------|
| 1 | `accounts` | `role` 추가 | 권한/역할 필드 추가 |
| 2 | `accounts` | `is_watchlist_public` 추가 | 관심종목 공개 여부 |
| 3 | `user_interactions` | `name` 추가 | 프로필/상호작용 이력 확장 |
| 4 | `user_interactions` | `market` 추가 | 종목 시장 정보 저장 |
| 5 | `analysis_logs` | `article_published_at` 추가 | 분석 로그 메타데이터 확장 |
| 6 | `analysis_logs` | `source_name` 추가 | 분석 로그 메타데이터 확장 |

중요 포인트:

- 이 변경들은 revision 이력이 아니라 **앱 기동 시점 SQL** 이었다.
- 실패해도 서비스는 계속 뜰 수 있도록 warning 처리되어 있어, 스키마 누락을 늦게 발견할 위험이 있었다.
- `saved_articles` 관련 보정은 baseline `832b942b94aa` 와 후속 revision `e86b70f9bed8` 검증 이후 `_run_column_migrations()` 에서 제거했다.
- 남은 6개 항목도 로컬 `multi_agent_db` 와 ORM 기준으로 모두 존재함을 확인한 뒤 로컬 브랜치에서 제거했다.
- 즉, 현재 로컬 브랜치 기준으로는 MySQL runtime column migration 호환 레이어가 제거된 상태다.

---

## 2-3. 현재 ORM 기준 테이블 inventory

참고 스냅샷:

- `docs/db/MYSQL-SCHEMA-SNAPSHOT-20260418.sql`
- `docs/db/MYSQL-SCHEMA-DRIFT-DECISIONS-20260418.md`
- `docs/db/MYSQL-BASELINE-STAMP-RUNBOOK-20260418.md`
- `docs/db/MYSQL-RUNTIME-MIGRATION-REMOVAL-CHECKLIST-20260418.md`

## MySQL (`Base`) 테이블

현재 ORM 기준 MySQL 테이블은 아래 21개다.

- `accounts`
- `analysis_logs`
- `boards`
- `card_comments`
- `card_likes`
- `investment_news`
- `investment_youtube_logs`
- `investment_youtube_videos`
- `market_videos`
- `notifications`
- `posts`
- `raw_articles`
- `saved_articles`
- `shared_cards`
- `stocks`
- `stock_themes`
- `user_interactions`
- `user_profiles`
- `video_comments`
- `watchlist_items`
- `youtube_videos`

## PostgreSQL (`PgBase`) 테이블

현재 ORM 기준 PostgreSQL 테이블은 아래 4개다.

- `analysis_cache`
- `interest_article_contents`
- `investment_news_contents`
- `investment_youtube_video_comments`

해석:

- 정형 데이터는 대부분 MySQL
- JSONB/비정형 저장은 PostgreSQL
- 즉, 현재 운영 기준 migration 우선순위는 **MySQL이 먼저**다

---

## 2-4. 문서와 실제 상태의 차이

### 문서상 의도

확인 파일:
- `docs/db/alembic-guide.md`
- `docs/db/README.md`
- `docs/db/env.py`

문서상 의도는 명확하다.

- MySQL에 Alembic 적용
- `docs/db/env.py` 를 `alembic/env.py` 로 복사
- `alembic revision --autogenerate`
- `create_all()` 제거

### 실제 상태

하지만 현재 실제 저장소 상태는 다르다.

- 실제 `alembic/env.py` 는 `PgBase.metadata` 를 바라봄
- `alembic/versions/` 는 비어 있음
- `main.py` 에서는 여전히 MySQL `create_all()` 과 `_run_column_migrations()` 가 실행됨

즉:

- **문서는 MySQL Alembic 전환이 "예정/지향" 상태**
- **실제 코드는 아직 전환 완료 전 상태**

이 차이를 먼저 문서로 고정해 두어야 한다.

---

## 3. 위험 분석

현재 구조의 주요 위험은 다음과 같다.

### 위험 1. 런타임 중 암묵적 스키마 변경

앱을 띄우는 순간 테이블 생성과 컬럼 추가가 수행된다.

문제:

- 배포와 스키마 변경이 분리되지 않음
- 앱 기동 실패 원인 분리가 어려움
- 운영자 입장에서 언제 스키마가 바뀌는지 추적하기 어려움

### 위험 2. 환경별 drift

개발자마다 DB 상태가 다를 수 있다.

문제:

- 어떤 환경은 컬럼이 있고
- 어떤 환경은 컬럼이 없고
- 어떤 환경은 인덱스가 다를 수 있다

### 위험 3. rollback 부재

현재 수동 SQL 보정은 버전 관리가 아니다.

문제:

- "이전 버전으로 되돌리기"가 어려움
- 문제가 생겼을 때 재현 가능한 rollback 경로가 없음

### 위험 4. MySQL / PostgreSQL migration 기준 불일치

현재 Alembic 대상은 PostgreSQL인데, 실제 운영상 중요한 정형 데이터 변경은 MySQL 쪽에 몰려 있다.

문제:

- 실제로 많이 바뀌는 DB와 migration 도구의 중심이 다름

---

## 4. 권장 baseline 전략

## 4-1. 우선순위

1. **MySQL baseline 먼저**
2. 기존 환경 stamp 전략 확정
3. 신규 변경부터 revision-only 원칙 적용
4. 안정화 후 `create_all()` / `_run_column_migrations()` 제거

## 4-2. 왜 MySQL 먼저인가

- 운영상 주요 정형 테이블이 MySQL에 있음
- 현재 수동 column migration도 전부 MySQL 대상
- 사용자 기능과 직접 연결된 대부분의 schema risk가 MySQL에 집중됨

PostgreSQL은 그 다음 단계에서 별도 migration 전략을 정리해도 된다.

---

## 4-3. baseline 생성 방식 권장안

권장 방식은 아래와 같다.

### 권장안: "full initial schema revision + 기존 DB stamp"

1. MySQL 기준 Alembic env를 실제 실행 가능 상태로 정리
2. 현재 `Base.metadata` 전체를 기준으로 **initial schema revision** 생성
3. 생성된 revision 내용을 수동 검토
4. **새 DB** 에는 `alembic upgrade head`
5. **기존 운영 DB** 는 백업 후 `alembic stamp <initial_revision>`
6. 이후부터는 신규 schema 변경을 revision으로만 추가

이 방식의 장점:

- 새 환경 bootstrap이 가능
- 기존 운영 DB는 테이블 재생성 없이 revision 이력만 맞출 수 있음
- 장기적으로 가장 표준적인 전환 경로

주의:

- initial revision은 자동 생성 후 반드시 검토해야 한다
- 인덱스명, unique key, foreign key는 autogenerate가 완벽하지 않을 수 있다

---

## 4-4. 왜 `stamp` 가 필요한가

현재 운영 DB는 이미 데이터가 있는 상태일 가능성이 높다.

이때 initial schema revision을 그대로 `upgrade` 하면:

- 기존 테이블 생성 시도
- 이미 있는 컬럼/인덱스와 충돌

따라서 기존 DB는:

- 실제 구조가 initial revision과 동일하다고 확인한 뒤
- `upgrade` 가 아니라 `stamp` 로 버전만 맞춘다

즉,

- 새 DB: `upgrade head`
- 기존 DB: `stamp <baseline>`

이 전략이 가장 안전하다.

---

## 5. 단계별 실행안

## Step 1. 현재 MySQL 실제 스키마 dump 확보

필수:

- 운영 DB 백업
- `SHOW CREATE TABLE` 또는 schema dump 확보
- ORM 기준과 실제 DB 기준 차이 비교

산출물:

- 테이블/컬럼/인덱스 차이표

## Step 2. MySQL Alembic 실행 경로 정리

해야 할 일:

- MySQL용 `alembic/env.py` 경로 확정
- ORM import 목록 최신화
- `alembic.ini` / env 파일이 실제 MySQL DB를 바라보게 정리

현재 상태상 선택지는 두 가지다.

### 선택지 A. 현재 `alembic/` 를 MySQL 기준으로 전환

장점:
- 단순함

단점:
- PostgreSQL 전략과 충돌 가능성

### 선택지 B. MySQL / PostgreSQL migration 경로 분리

예:
- `alembic_mysql/`
- `alembic_pg/`

장점:
- 저장소가 두 DB의 책임을 명확히 구분 가능

단점:
- 초기 설정이 조금 더 큼

현재 프로젝트 상황에서는 **단기적으로 A 또는 "하나의 alembic + db별 옵션 분기"**, 중장기적으로는 **분리 구조**가 더 깔끔하다.

## Step 3. initial schema revision 생성

권장:

- 로컬 빈 MySQL에서 autogenerate 수행
- 결과를 수동 검토

체크 포인트:

- 21개 MySQL 테이블이 모두 생성 대상에 포함되는지
- foreign key / unique index / default 값이 정확한지
- `main.py` 수동 migration 항목이 ORM에 이미 반영되어 있는지

## Step 4. existing DB stamp 절차 문서화

기존 운영 DB 대상 절차:

1. 운영 DB 백업
2. initial revision 내용과 실제 schema 비교
3. 차이 없으면 `alembic stamp <initial_rev>`
4. 이후 신규 migration부터 `upgrade head`

## Step 5. 런타임 schema 변경 제거

제거 순서 권장:

1. 신규 schema 변경부터 revision-only 적용
2. `_run_column_migrations()` 를 "호환 레이어"로 한시 유지
3. 모든 대상 DB가 최소 `f84b02321df9` 까지 정렬됐는지 확인
4. 1~2 배포 주기 동안 문제 없으면 남은 6개 수동 컬럼 보정 제거
5. 마지막에 `Base.metadata.create_all()` 제거

주의:

- `create_all()` 을 너무 일찍 제거하면 신규 로컬 환경이 깨질 수 있다
- baseline revision + onboarding 문서가 준비된 뒤 제거해야 한다
- 오래된 DB가 아직 `stamp/upgrade` 되지 않았다면 `_run_column_migrations()` 제거는 미룬다

실행 체크리스트:

- 실제 제거 전에는 `docs/db/MYSQL-RUNTIME-MIGRATION-REMOVAL-CHECKLIST-20260418.md` 기준으로
  모든 대상 DB가 최소 `f84b02321df9` 까지 정렬되었는지 확인한다

로컬 전용 실행 결과:

- 사용자 요청에 따라 운영 환경 대신 로컬 기준으로만 진행했다
- readiness 체크를 통과한 뒤 `main.py` 에서 남은 6개 runtime column migration 을 제거했다
- scratch DB에서 `alembic upgrade head` bootstrap 성공을 확인한 뒤 `Base.metadata.create_all()` 도 제거했다

---

## 6. 이번 inventory 기준 즉시 해야 할 일

### 필수

1. MySQL 실제 schema snapshot 확보
2. MySQL initial schema revision 생성 실험
3. `alembic/versions/` 첫 revision 생성
4. `main.py` manual migration 목록과 initial revision 차이 대조

### 그 다음

5. 운영 DB stamp 절차 문서화
6. `_run_column_migrations()` 제거 일정 수립
7. `create_all()` 제거 일정 수립

---

## 7. 2026-04-18 dry-run 결과

이번 작업에서 아래 dry-run을 실제로 수행했다.

### 수행 내용

- MySQL schema snapshot 생성
  - `docs/db/MYSQL-SCHEMA-SNAPSHOT-20260418.sql`
- MySQL 전용 Alembic dry-run 경로 분리
  - `alembic_mysql.ini`
  - `alembic_mysql/env.py`
  - `alembic_mysql/script.py.mako`
- scratch DB 생성
  - `multi_agent_migration_dryrun`
- initial revision 초안 생성
  - `alembic_mysql/versions/832b942b94aa_mysql_initial_schema_dryrun.py`

### 결과

- **initial revision 초안 생성 자체는 성공**
- **하지만 현재 ORM과 실제 live schema snapshot 사이에 drift가 있어 바로 운영 DB를 stamp 하기는 위험**

### dry-run에서 확인한 대표 drift

| 영역 | ORM 기준 | 실제 schema snapshot | 판단 |
|------|----------|----------------------|------|
| `watchlist_items.symbol` | `String(20)` | `varchar(6)` | 길이 불일치 조정 필요 |
| `card_likes` | `uq_card_like_ip` + `uq_card_like_account` | `uq_card_like_ip`만 존재 | ORM/실DB 정책 차이 확인 필요 |
| `saved_articles.account_id` | `index=True` | 별도 인덱스 없음 | ORM에만 인덱스 정의 존재 |
| `analysis_logs.source_type` | `String(20)` | `varchar(50)` | 길이 불일치 조정 필요 |

추가 메모:

- dry-run 중 scratch DB에는 `alembic_version` 테이블만 생성되었고, 애플리케이션 스키마는 적용되지 않았다.
- 즉, 이번 단계는 운영 DB나 실제 앱 스키마를 변경하지 않고 revision 초안만 생성한 상태다.

### 해석

이 결과는 두 가지를 의미한다.

1. MySQL initial revision 생성 경로는 이제 실제로 동작한다.
2. 하지만 baseline 전환 전에 **ORM 정의와 실제 운영 스키마 차이부터 먼저 정리**해야 한다.

즉, 다음 단계는 `stamp` 가 아니라:

- drift 항목 확정
- 어떤 쪽을 정답으로 삼을지 결정
- ORM 또는 schema를 먼저 맞춘 뒤 revision 재생성

이 순서가 되어야 한다.

### 후속 정리 결과

이후 drift 판정을 거쳐 baseline 후보 revision을 live schema 기준으로 수동 보정했다.

대상 파일:

- `alembic_mysql/versions/832b942b94aa_mysql_initial_schema_dryrun.py`

보정 후 scratch DB 재생성 + `upgrade head` 검증 결과:

- **새 DB bootstrap 성공**
- live DB와의 남은 차이는 대부분 아래 수준으로 축소됨
  - `AUTO_INCREMENT` 현재 값
  - `alembic_version` 테이블 존재 여부
  - 컬럼 순서
  - 일부 MySQL이 자동 생성한 내부 index / constraint naming 세부 차이

즉, 현재 revision은 **운영 reality를 반영한 baseline candidate** 로 볼 수 있다.

다음 실제 작업은 더 이상 autogenerate가 아니라:

1. baseline candidate를 정식 revision으로 확정할지 결정
2. 운영 DB `stamp` 절차를 실행 가능한 runbook으로 문서화
3. 이후 drift 정리를 별도 revision으로 분리

이 순서가 된다.

### 로컬 적용 결과

이후 로컬 `multi_agent_db` 에 대해 baseline stamp를 실제 수행했고, 후속 revision들도 검증했다.

- baseline stamp:
  - revision: `832b942b94aa`
- 첫 후속 revision:
  - revision: `e86b70f9bed8`
  - 내용: `saved_articles.account_id` 비고유 인덱스 추가
- 둘째 후속 revision:
  - revision: `f84b02321df9`
  - 내용: `card_likes.uq_card_like_account` unique constraint 추가

현재 로컬 MySQL 기준 Alembic 상태:

- `alembic current` 결과: `f84b02321df9 (head)`
- `saved_articles` 에 `ix_saved_articles_account_id` 존재 확인
- `card_likes` 에 `uq_card_like_account` 존재 확인
- `analysis_log_orm.py` 의 `source_type` 길이를 live schema 기준 `String(50)` 으로 정렬 완료
- `watchlist` 경로의 symbol 길이를 live schema 기준 `6`으로 정렬 완료
- `accounts`, `user_interactions`, `analysis_logs` 의 남은 runtime 컬럼 보정 6개는 로컬 live DB/ORM 기준 충족 확인 후 `main.py` 에서 제거 완료
- scratch DB `multi_agent_createall_removal_check` 에서 `alembic upgrade head` 성공 확인 후 MySQL `Base.metadata.create_all()` 제거 완료

즉, baseline 전환은 문서 단계가 아니라 **로컬 DB에서 실제 후속 revision 체인까지 검증된 상태**다.

---

## 8. Definition of Done

아래 조건을 만족하면 "MySQL migration baseline 정리" 1차 완료로 본다.

- MySQL initial schema revision이 실제 저장소에 존재한다
- 기존 DB baseline `stamp` 절차가 문서화되고 로컬에서 실제 검증되었다
- 신규 DB는 `alembic upgrade head` 로 기동 가능하다
- baseline 이후 후속 revision 추가/적용 경로가 실제로 검증되었다
- 신규 schema 변경은 더 이상 `main.py` 수동 SQL에 추가하지 않는다
- `create_all()` / `_run_column_migrations()` 제거 계획이 문서화되었다

---

## 9. 최종 판단

지금 상태에서 바로 `main.py` 의 `create_all()` 을 지우는 것은 위험하다.

먼저 해야 할 것은:

- **baseline revision 만들기**
- **기존 DB stamp 전략 확정**
- **MySQL을 migration 운영의 기준 DB로 고정**

즉, 이번 정리의 첫 실제 산출물은 코드 삭제가 아니라 다음 두 가지다.

1. MySQL initial schema revision
2. existing DB stamp 절차

이 두 가지가 준비되면 그 다음에야 `main.py` 의 수동 schema 변경 로직을 안전하게 걷어낼 수 있다.
