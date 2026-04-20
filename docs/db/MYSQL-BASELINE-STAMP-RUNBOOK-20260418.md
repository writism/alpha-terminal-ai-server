# MySQL Baseline Stamp Runbook

> 작성일: 2026-04-18
> 대상 저장소: `alpha-terminal-ai-server`
> 목적: 기존 MySQL DB에 baseline revision을 **schema 변경 없이** 안전하게 등록하는 절차를 표준화한다.

---

## 1. 이 문서의 역할

이 문서는 기존 운영/로컬 MySQL DB에 대해 아래 작업을 수행할 때 사용한다.

- 이미 스키마와 데이터가 존재하는 DB에
- baseline revision을 **적용(upgrade)** 하지 않고
- baseline revision을 **버전 정보만 기록(stamp)** 하는 절차

핵심 원칙:

- `stamp` 는 스키마를 바꾸지 않는다.
- `stamp` 는 `alembic_version` 테이블에 baseline revision 번호를 기록한다.
- 따라서 `stamp` 전에 **현재 DB 구조가 baseline candidate와 실질적으로 같다는 전제**가 필요하다.

---

## 2. 기준 파일

이 runbook은 아래 파일을 기준으로 한다.

- baseline candidate revision:
  - `alembic_mysql/versions/832b942b94aa_mysql_initial_schema_dryrun.py`
- MySQL Alembic config:
  - `alembic_mysql.ini`
  - `alembic_mysql/env.py`
- 기준 스키마 스냅샷:
  - `docs/db/MYSQL-SCHEMA-SNAPSHOT-20260418.sql`
- drift 판단 문서:
  - `docs/db/MYSQL-SCHEMA-DRIFT-DECISIONS-20260418.md`
- inventory / baseline 계획:
  - `docs/db/MYSQL-MIGRATION-INVENTORY-AND-BASELINE-PLAN-20260418.md`
- runtime migration 제거 체크리스트:
  - `docs/db/MYSQL-RUNTIME-MIGRATION-REMOVAL-CHECKLIST-20260418.md`

기준 baseline revision 번호:

- `832b942b94aa`

---

## 3. 언제 사용해야 하는가

이 runbook은 아래 조건을 만족할 때만 사용한다.

1. 대상 DB가 이미 운영 중이거나 데이터가 있는 기존 DB다.
2. 대상 DB 스키마가 baseline candidate와 의미 있는 수준에서 일치한다.
3. baseline을 등록한 뒤부터 신규 schema 변경을 Alembic revision으로 관리할 계획이다.

아래 경우에는 사용하지 않는다.

- 대상 DB가 빈 DB인 경우
  - 이 경우 `stamp` 가 아니라 `upgrade head` 사용
- 대상 DB가 baseline candidate와 구조적으로 다른 경우
  - 먼저 drift 정리 필요
- baseline revision 파일이 아직 확정되지 않은 경우

---

## 4. 사전 조건

## 필수

1. 대상 DB 백업 확보
2. `alpha-terminal-ai-server/.venv` 사용 가능
3. `alembic_mysql.ini` / `alembic_mysql/env.py` 준비 완료
4. baseline candidate revision 존재

## 권장

5. 앱 프로세스 일시 정지 또는 작업창 확보
6. schema-only dump 비교 결과 보관
7. 대상 DB 이름을 환경변수로 명시

---

## 5. 사전 점검 체크리스트

`stamp` 전에 아래를 반드시 확인한다.

- [ ] 대상 DB 이름이 맞는가
- [ ] 대상 DB가 MySQL 기준 DB인가
- [ ] `mysqldump --no-data` 결과를 확보했는가
- [ ] 현재 DB 구조가 baseline candidate와 의미 있게 같은가
- [ ] `card_likes`, `saved_articles`, `analysis_logs`, `watchlist_items` drift 판단이 문서와 일치하는가
- [ ] 데이터 백업 또는 최소 schema snapshot이 있는가

---

## 6. 추천 사전 백업 절차

## 6-1. schema-only 백업

```bash
docker exec mysql-container mysqldump \
  -u<user> -p"<password>" \
  --no-data --skip-comments --skip-dump-date \
  <target_db> > /tmp/<target_db>_schema_before_stamp.sql
```

## 6-2. full backup 권장

```bash
docker exec mysql-container mysqldump \
  -u<user> -p"<password>" \
  <target_db> > /tmp/<target_db>_full_before_stamp.sql
```

실운영 환경이라면 schema-only 백업만으로 끝내지 말고 full backup 확보를 권장한다.

---

## 7. 사전 검증 절차

## 7-1. 대상 DB 현재 테이블 확인

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "SHOW TABLES;"
```

## 7-2. 대상 DB에 이미 alembic_version 이 있는지 확인

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "SHOW TABLES LIKE 'alembic_version';"
```

판단:

- 없으면 baseline stamp 대상일 가능성이 높음
- 있으면 이미 Alembic 관리 중일 수 있으므로 바로 stamp 하지 말고 current/history 먼저 확인

## 7-3. baseline candidate와 의미 있는 차이 비교

권장 방식:

1. 대상 DB schema-only dump 생성
2. `docs/db/MYSQL-SCHEMA-SNAPSHOT-20260418.sql` 와 비교
3. 차이가 아래 수준인지 확인

허용 가능한 차이 예시:

- `AUTO_INCREMENT` 현재 값
- `alembic_version` 테이블 유무
- 컬럼 순서
- MySQL 내부 제약조건 이름 일부

즉시 중단해야 하는 차이 예시:

- 컬럼 타입 불일치
- 컬럼 누락
- unique/index 구조 불일치
- foreign key 구조 불일치

---

## 8. Stamp 실행 절차

## 8-1. 대상 DB 이름 지정

예시:

```bash
export ALEMBIC_MYSQL_DATABASE=<target_db>
```

## 8-2. 현재 Alembic 상태 확인

```bash
./.venv/bin/alembic -c alembic_mysql.ini current
```

주의:

- 기존 DB에서 `alembic_version` 이 없으면 아무 것도 나오지 않거나 baseline 전 상태로 보일 수 있다.
- 이건 비정상이라기보다 "아직 Alembic에 등록되지 않음"에 가깝다.

## 8-3. Baseline stamp 실행

```bash
ALEMBIC_MYSQL_DATABASE=<target_db> \
./.venv/bin/alembic -c alembic_mysql.ini stamp 832b942b94aa
```

이 명령은 schema 변경이 아니라 version 기록만 수행한다.

---

## 9. Stamp 후 검증

## 9-1. 버전 테이블 확인

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "SELECT version_num FROM alembic_version;"
```

기대 결과:

- `832b942b94aa`

## 9-2. Alembic current 재확인

```bash
ALEMBIC_MYSQL_DATABASE=<target_db> \
./.venv/bin/alembic -c alembic_mysql.ini current
```

기대 결과:

- 현재 DB revision이 `832b942b94aa` 로 표시

## 9-3. 앱 기동 확인

권장:

- 앱 시작
- 주요 API 헬스체크
- schema 관련 에러 로그가 없는지 확인

예:

```bash
python main.py
```

또는 기존 실행 방식에 맞춰 백엔드 기동 후 에러 로그 점검

---

## 10. 실패 시 중단 기준

아래 상황이면 즉시 중단한다.

1. `stamp` 전 schema diff에서 의미 있는 구조 차이가 발견됨
2. 대상 DB에 이미 다른 Alembic revision이 존재함
3. `stamp` 후 앱 기동 시 schema 관련 에러가 발생함
4. `main.py` 가 추가 수동 migration을 시도하며 예외를 발생시킴

중단 후 해야 할 일:

- 현재 dump 보관
- diff 결과 문서화
- baseline candidate 또는 live schema 정합성 재검토

---

## 11. 간단 롤백 절차

`stamp` 는 schema를 바꾸지 않고 `alembic_version` 만 기록하므로,
아직 후속 migration을 적용하지 않았다면 롤백은 비교적 단순하다.

### 방법 A. alembic_version 테이블 제거

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "DROP TABLE IF EXISTS alembic_version;"
```

### 방법 B. version row 삭제

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "DELETE FROM alembic_version WHERE version_num = '832b942b94aa';"
```

권장:

- 아직 Alembic을 정식 도입 전이라면 테이블 제거가 더 깔끔할 수 있다
- 이미 후속 revision까지 적용했다면 단순 제거/삭제는 사용하지 말고 revision 체계에 맞춰야 한다

---

## 12. 로컬/스크래치 검증용 예시

scratch DB 기준 검증 예시:

```bash
docker exec mysql-container mysql \
  -ueddi -p"eddi@123" \
  -e "DROP DATABASE IF EXISTS multi_agent_migration_dryrun; CREATE DATABASE multi_agent_migration_dryrun CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

ALEMBIC_MYSQL_DATABASE=multi_agent_migration_dryrun \
./.venv/bin/alembic -c alembic_mysql.ini upgrade head
```

주의:

- 위 예시는 **scratch DB** 검증용이다
- 기존 운영 DB에는 `upgrade head` 가 아니라 `stamp` 를 사용해야 한다

---

## 13. Stamp 이후 바로 해야 할 일

baseline 등록 이후에는 신규 schema 변경을 아래 순서로 관리한다.

1. drift 정리 revision 추가
   - ORM / live schema 정합화 항목
2. `main.py` 수동 migration 항목을 더 이상 늘리지 않기
3. 일정 기간 안정화 후 `create_all()` 제거 계획 실행
4. 최종적으로 `_run_column_migrations()` 제거

추가 메모:

- `saved_articles.account_id` 인덱스는 후속 revision `e86b70f9bed8` 로 이미 적용/검증했다.
- `card_likes.uq_card_like_account` 는 후속 revision `f84b02321df9` 로 이미 적용/검증했다.
- `watchlist` 경로 symbol 길이는 live schema 기준 `6`으로 코드 정합화를 마쳤다.
- 이에 따라 `saved_articles` 관련 수동 schema 보정은 `main.py` 에서 제거했다.

---

## 14. 최종 권장

운영 DB에 바로 이 runbook을 실행하기 전에 최소 한 번 더 확인해야 할 것은 아래 두 가지다.

1. 대상 DB의 최신 schema-only dump가 baseline candidate와 여전히 맞는가
2. `832b942b94aa` 를 정식 baseline revision 번호로 확정할 것인가

즉, 이 문서는 지금 바로 실DB를 건드리기 위한 문서라기보다,
**실행 직전 체크리스트와 표준 절차를 미리 고정한 runbook** 이다.

이 runbook이 준비된 상태라면, 다음 실무 단계는:

- 실제 대상 DB를 지정하고
- schema diff를 마지막으로 확인한 뒤
- `stamp 832b942b94aa`

까지 수행하는 것이다.

---

## 15. 2026-04-18 로컬 실행 기록

이 runbook 기준으로 로컬 MySQL DB에 대해 baseline stamp를 실제 수행했다.

대상 DB:

- `multi_agent_db`

사전 백업:

- `backups/multi_agent_db_20260418_194051_pre_stamp.sql.gz`

실행 명령:

```bash
ALEMBIC_MYSQL_DATABASE=multi_agent_db \
./.venv/bin/alembic -c alembic_mysql.ini stamp 832b942b94aa
```

실행 후 검증 결과:

- `SELECT version_num FROM alembic_version;`
  - 결과: `832b942b94aa`
- `alembic current`
  - 결과: `832b942b94aa (head)`

의미:

- 로컬 `multi_agent_db`는 이제 baseline revision이 등록된 상태다.
- 이번 작업은 `stamp` 이므로 스키마 변경이 아니라 `alembic_version` 등록 작업이다.
