# MySQL Runtime Migration Removal Checklist

> 작성일: 2026-04-18
> 대상 저장소: `alpha-terminal-ai-server`
> 목적: `main.py` 의 `_run_column_migrations()` 와 이후 `Base.metadata.create_all()` 제거 가능 시점을 환경별로 판정한다.

---

## 1. 이 문서의 역할

이 문서는 아래 두 작업을 하기 전에 사용한다.

1. `main.py` 의 남은 runtime column migration 제거
2. 마지막 단계의 `Base.metadata.create_all()` 제거

현재 원칙:

- 신규 schema 변경은 Alembic revision으로만 관리한다.
- 이 문서는 `_run_column_migrations()` 제거 전 판정 기준과 제거 직전 체크리스트를 기록한다.
- 따라서 제거 여부는 "로컬에서 잘 된다"가 아니라 **모든 대상 DB가 최소 기준 revision까지 정렬되었는지**로 판단해야 한다.

---

## 2. 현재 제거 대상

제거 직전 `main.py` 의 runtime column migration 대상은 아래 6개였다.

1. `accounts.role`
2. `accounts.is_watchlist_public`
3. `user_interactions.name`
4. `user_interactions.market`
5. `analysis_logs.article_published_at`
6. `analysis_logs.source_name`

이 6개는 로컬 `multi_agent_db` 에서는 이미 모두 존재하며, ORM에도 반영되어 있다.

---

## 3. 최소 기준 revision

runtime migration 제거 판단 기준으로 사용하는 최소 Alembic revision:

- `832b942b94aa`
  - MySQL baseline
- `e86b70f9bed8`
  - `saved_articles.account_id` index
- `f84b02321df9`
  - `card_likes.uq_card_like_account`

실제 제거 판단에 사용할 최소 기준은 아래와 같다.

- **모든 대상 DB가 최소 `f84b02321df9` 까지 정렬되어 있어야 한다**

이유:

- baseline 이후 필수 drift 정리 revision이 이미 이어졌고
- 현재 로컬 검증 기준 head가 `f84b02321df9` 이기 때문이다

---

## 4. 대상 환경별 체크리스트

환경마다 아래 체크리스트를 반복한다.

### 4-1. Alembic 버전 확인

```bash
export ALEMBIC_MYSQL_DATABASE=<target_db>
./.venv/bin/alembic -c alembic_mysql.ini current
```

자동 점검 스크립트:

```bash
ALEMBIC_MYSQL_DATABASE=<target_db> \
./.venv/bin/python docs/db/check_mysql_runtime_migration_readiness.py
```

기대 결과:

- `f84b02321df9 (head)`

추가 확인:

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "SELECT version_num FROM alembic_version;"
```

기대 결과:

- `f84b02321df9`

### 4-2. 남은 6개 컬럼 존재 확인

```sql
SELECT TABLE_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (
    (TABLE_NAME = 'accounts' AND COLUMN_NAME IN ('role', 'is_watchlist_public'))
    OR
    (TABLE_NAME = 'user_interactions' AND COLUMN_NAME IN ('name', 'market'))
    OR
    (TABLE_NAME = 'analysis_logs' AND COLUMN_NAME IN ('article_published_at', 'source_name'))
  )
ORDER BY TABLE_NAME, COLUMN_NAME;
```

기대 결과:

- 총 6행 반환

### 4-3. 핵심 후속 drift 반영 여부 확인

```bash
docker exec mysql-container mysql \
  -u<user> -p"<password>" \
  -D <target_db> \
  -e "SHOW INDEX FROM saved_articles; SHOW INDEX FROM card_likes;"
```

기대 결과:

- `saved_articles` 에 `ix_saved_articles_account_id`
- `card_likes` 에 `uq_card_like_account`

### 4-4. 신규 DB bootstrap 검증

빈 DB 또는 scratch DB에서 아래가 가능해야 한다.

```bash
export ALEMBIC_MYSQL_DATABASE=<scratch_db>
./.venv/bin/alembic -c alembic_mysql.ini upgrade head
```

기대 결과:

- 실패 없이 head까지 적용

이 단계는 `create_all()` 제거 전 특히 중요하다.

---

## 5. 중단 기준

아래 상황이면 `_run_column_migrations()` 제거를 미룬다.

1. 어떤 대상 DB라도 `alembic_version` 이 없거나 `f84b02321df9` 보다 뒤처져 있음
2. 남은 6개 컬럼 중 하나라도 실제 DB에 없음
3. `saved_articles` 또는 `card_likes` 후속 revision 결과가 일부 환경에 반영되지 않음
4. 신규 DB `upgrade head` 가 실패함
5. 최근 배포 로그에서 schema 관련 warning / error 가 반복됨

---

## 6. 제거 실행 순서

체크리스트를 모두 통과하면 아래 순서로 진행한다.

1. 모든 대상 DB의 현재 revision 기록
2. 부족한 환경은 `stamp` 또는 `upgrade head` 로 `f84b02321df9` 까지 정렬
3. `main.py` 에서 남은 6개 runtime column migration 제거
4. non-prod 또는 가장 안전한 환경에 먼저 배포
5. 1~2 배포 주기 동안 schema warning / startup failure 없는지 확인
6. 문제 없으면 동일 원칙으로 `Base.metadata.create_all()` 제거 검토

중요:

- `_run_column_migrations()` 제거와 `create_all()` 제거를 한 번에 묶지 않는다.
- 두 단계는 반드시 분리한다.

---

## 7. 로컬 기준 현재 상태

2026-04-18 로컬 `multi_agent_db` 기준 확인 결과:

- `alembic current`: `f84b02321df9 (head)`
- `saved_articles`: `ix_saved_articles_account_id` 존재
- `card_likes`: `uq_card_like_account` 존재
- 남은 6개 runtime column migration 대상 컬럼 존재 확인

즉, 로컬 환경은 **runtime migration 제거 후보 상태**였고,
사용자 요청에 따라 로컬 전용 기준으로 `main.py` 에서 해당 호환 레이어를 제거했다.

---

## 8. 다음 실제 작업

이 문서 기준 다음 실제 작업은 아래 둘 중 하나다.

1. 다른 환경에도 동일 기준을 적용할지 결정한다
2. 별도 검증이 끝나면 마지막 단계인 `Base.metadata.create_all()` 제거를 검토한다

로컬 전용 실행 메모:

- scratch DB에서 `alembic upgrade head` bootstrap 확인 후 MySQL `Base.metadata.create_all()` 제거까지 완료했다

현재 상태 기록 문서:

- `docs/db/MYSQL-RUNTIME-MIGRATION-READINESS-STATUS-20260418.md`
- 자동 점검 스크립트: `docs/db/check_mysql_runtime_migration_readiness.py`
