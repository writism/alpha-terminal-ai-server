# MySQL Runtime Migration Readiness Status

> 작성일: 2026-04-18
> 대상 저장소: `alpha-terminal-ai-server`
> 목적: `_run_column_migrations()` 제거 판단을 위한 환경별 현재 상태를 기록한다.

---

## 1. 요약

현재 확인 결과는 아래와 같다.

| 환경 | 접근 가능 여부 | 현재 상태 | 제거 판단 |
|------|----------------|-----------|-----------|
| 로컬 `multi_agent_db` | 가능 | 체크리스트 충족 후 runtime migration 제거 + MySQL `create_all()` 제거 완료 | 완료 |
| AWS EC2 운영 환경 | 이번 작업 범위 제외 | 실행 명령 준비만 완료 | 미적용 |

즉, **로컬 전용 기준으로는 MySQL runtime schema compatibility layer 제거를 완료했고**, 운영 환경은 이번 작업 범위에 포함하지 않았다.

---

## 2. 환경 식별 결과

### 로컬

- `.env` 기준 MySQL DB: `multi_agent_db`
- 접속 형태: 로컬 Docker MySQL (`mysql-container`)

### AWS EC2 운영 환경

문서 기준으로 아래는 확인됐다.

- 배포 위치: `/home/ec2-user/alpha-terminal-ai-server`
- API 컨테이너: `alphadesk-api`
- self-hosted runner 기반 자동 배포 사용

다만 운영 MySQL 토폴로지는 문서 간 표현이 완전히 일치하지 않는다.

- 일부 문서: `alphadesk-mysql` 컨테이너 기준 점검
- 다른 문서: RDS 운영 중으로 표기

따라서 운영 환경 첫 점검 명령은 **`alphadesk-api` 컨테이너에서 실제 `MYSQL_HOST`를 읽는 것**으로 시작해야 한다.

---

## 3. 로컬 점검 결과

### 3-1. Alembic revision

확인 결과:

- `alembic current`: `f84b02321df9 (head)`

### 3-2. 남은 runtime column migration 6개

확인 결과:

- `accounts.role`
- `accounts.is_watchlist_public`
- `user_interactions.name`
- `user_interactions.market`
- `analysis_logs.article_published_at`
- `analysis_logs.source_name`

총 6개 모두 존재 확인.

### 3-3. 후속 drift 반영 여부

확인 결과:

- `saved_articles` 에 `ix_saved_articles_account_id` 존재
- `card_likes` 에 `uq_card_like_account` 존재

### 3-4. 결론

로컬 `multi_agent_db` 는 `docs/db/MYSQL-RUNTIME-MIGRATION-REMOVAL-CHECKLIST-20260418.md` 기준으로
runtime migration 제거 후보 상태였고, 이후 실제로 `main.py` 에서 호환 레이어를 제거했다.

자동 점검 실행 기록:

```bash
./.venv/bin/python docs/db/check_mysql_runtime_migration_readiness.py
```

결과:

- `Overall result: READY_TO_REMOVE_RUNTIME_MIGRATIONS`

---

## 4. EC2 운영 환경 점검 명령

아래 명령은 **EC2 호스트에서** 실행한다.

가장 빠른 방법:

```bash
cd /home/ec2-user/alpha-terminal-ai-server
./.venv/bin/python docs/db/check_mysql_runtime_migration_readiness.py
```

위 스크립트는 현재 `.env` 기준 MySQL 설정으로 아래를 한 번에 확인한다.

- `alembic current`
- `alembic_version`
- 남은 6개 runtime column migration 대상 컬럼
- `saved_articles` / `card_likes` 후속 drift 반영 여부

### 4-1. 운영 MySQL 접속 형태 확인

```bash
docker exec alphadesk-api printenv MYSQL_HOST
docker exec alphadesk-api printenv MYSQL_DATABASE
docker exec alphadesk-api printenv MYSQL_USER
```

판단:

- `MYSQL_HOST` 가 컨테이너명 또는 `localhost` 계열이면 Docker MySQL일 가능성이 높다
- `MYSQL_HOST` 가 AWS 엔드포인트면 RDS일 가능성이 높다

### 4-2. Alembic 현재 버전 확인

```bash
cd /home/ec2-user/alpha-terminal-ai-server
MYSQL_DATABASE=$(grep '^MYSQL_DATABASE=' .env | cut -d= -f2-)
ALEMBIC_MYSQL_DATABASE="$MYSQL_DATABASE" ./.venv/bin/alembic -c alembic_mysql.ini current
```

기대 결과:

- `f84b02321df9 (head)`

### 4-3. 버전 테이블 직접 확인

MySQL이 컨테이너라면:

```bash
MYSQL_C=$(docker ps --filter ancestor=mysql:8.0 --format '{{.Names}}' | sed -n '1p')
MYSQL_USER=$(docker exec alphadesk-api printenv MYSQL_USER)
MYSQL_PASSWORD=$(docker exec alphadesk-api printenv MYSQL_PASSWORD)
MYSQL_DATABASE=$(docker exec alphadesk-api printenv MYSQL_DATABASE)

docker exec "$MYSQL_C" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
  -e "SELECT version_num FROM alembic_version;"
```

MySQL이 외부 호스트(RDS 등)라면:

```bash
MYSQL_HOST=$(docker exec alphadesk-api printenv MYSQL_HOST)
MYSQL_USER=$(docker exec alphadesk-api printenv MYSQL_USER)
MYSQL_PASSWORD=$(docker exec alphadesk-api printenv MYSQL_PASSWORD)
MYSQL_DATABASE=$(docker exec alphadesk-api printenv MYSQL_DATABASE)

mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
  -e "SELECT version_num FROM alembic_version;"
```

기대 결과:

- `f84b02321df9`

### 4-4. 남은 6개 컬럼 / 후속 drift 확인

컨테이너형 MySQL이면 `docker exec "$MYSQL_C" mysql ...`, 외부 호스트면 `mysql -h"$MYSQL_HOST" ...`로 아래 SQL을 실행한다.

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

SHOW INDEX FROM saved_articles;
SHOW INDEX FROM card_likes;
```

기대 결과:

- 컬럼 조회 6행
- `saved_articles` 에 `ix_saved_articles_account_id`
- `card_likes` 에 `uq_card_like_account`

---

## 5. 제거 결정 규칙

아래 조건을 모두 만족하면 `_run_column_migrations()` 제거를 진행할 수 있다.

1. 로컬 점검 통과
2. 운영 환경 `alembic current` 가 `f84b02321df9 (head)`
3. 운영 환경 `alembic_version` 이 `f84b02321df9`
4. 운영 환경에 남은 6개 컬럼이 모두 존재
5. 운영 환경에 `saved_articles` / `card_likes` 후속 drift 반영이 모두 존재

하나라도 미충족이면 제거를 미룬다.

---

## 6. 현재 결론

2026-04-18 현재 결론:

- 로컬: `_run_column_migrations()` 제거 완료, MySQL `Base.metadata.create_all()` 제거 완료
- EC2 운영: **점검 명령 준비 완료, 이번 범위에서는 미적용**

따라서 현재 브랜치 상태는 **로컬 전용 기준으로 MySQL runtime schema compatibility layer 제거 완료**다.
