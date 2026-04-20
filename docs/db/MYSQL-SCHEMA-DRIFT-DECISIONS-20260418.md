# MySQL Schema Drift Decisions

> 작성일: 2026-04-18
> 대상: `alpha-terminal-ai-server`
> 기준 자료:
> - `docs/db/MYSQL-SCHEMA-SNAPSHOT-20260418.sql`
> - `alembic_mysql/versions/832b942b94aa_mysql_initial_schema_dryrun.py`
> - live MySQL 조회 결과

---

## 1. 목적

이 문서는 MySQL baseline 전환 전에 확인된 주요 schema drift 항목에 대해,

- 무엇이 live DB 기준인지
- 무엇이 ORM 기준인지
- baseline에는 어느 쪽을 반영해야 하는지
- 후속 revision에서 무엇을 바꿔야 하는지

를 결정하기 위한 문서다.

핵심 원칙은 하나다.

**안전 우선 baseline은 "현재 운영 스키마를 재현 가능한 상태"에 맞추고, 이상적인 구조 정리는 후속 revision으로 분리한다.**

즉, baseline 단계에서 live DB와 ORM이 다르면 무조건 ORM을 따르지 않는다.
먼저 **existing DB stamp가 가능한 형태**를 만들고, 그 다음 정리 revision을 쌓는다.

---

## 2. 공통 결론

현재 dry-run 결과를 보면, MySQL initial revision 경로 자체는 정상 동작한다.

확인 사실:

- scratch DB `multi_agent_migration_dryrun` 생성 성공
- MySQL initial revision autogenerate 성공
- scratch DB에 `alembic upgrade head` 성공
- 새 DB bootstrap 경로는 검증됨

하지만 운영 DB에 바로 `stamp` 가능한 수준은 아니다.

이유:

- ORM metadata와 live schema가 일부 다르다
- 따라서 생성된 dry-run revision을 그대로 baseline으로 삼으면 existing DB와 충돌한다

따라서 안전한 전략은 다음과 같다.

1. **baseline revision은 live schema 기준으로 맞춘다**
2. **drift 정리는 후속 revision으로 나눈다**

---

## 3. Drift 결정표

| 항목 | live DB | ORM / dry-run | 증거 | baseline 기준 | 후속 조치 |
|------|---------|---------------|------|---------------|-----------|
| `watchlist_items.symbol` 길이 | `varchar(6)` | `String(20)` | live table / ORM / dry-run 비교 | **live 기준 채택** | ORM 정합성 재검토 또는 후속 widening |
| `card_likes.uq_card_like_account` | 없음 | 있음 | live/dry-run 비교 + repository 로직 | **live 기준 채택** | 후속 revision으로 unique 추가 검토 |
| `saved_articles.account_id` 인덱스 | 없음 | 있음 | live/dry-run 비교 + query usage | **live 기준 채택** | 후속 revision으로 index 추가 권장 |
| `analysis_logs.source_type` 길이 | `varchar(50)` | `String(20)` | live/dry-run 비교 + 실제 값 조회 | **live 기준 채택** | ORM을 50으로 맞추거나 후속 shrink 결정 |

---

## 4. 항목별 판단

## 4-1. `watchlist_items.symbol`

### 현재 상태

- live DB: `varchar(6)`
- baseline 당시 ORM: `String(20)`

### 추가 확인

실제 데이터 기준:

- `watchlist_items.symbol` 최대 길이: `6`
- `stocks.symbol` 최대 길이: `6`

즉, 현재 운영 데이터만 보면 live DB `varchar(6)` 범위를 벗어나지 않는다.

### 해석

이 항목은 두 가지 해석이 가능하다.

1. ORM이 미래 확장을 고려해 넓혀 놓은 상태
2. live DB가 현재 운영 도메인 기준을 더 잘 반영한 상태

안전 우선 관점에서는 현재 바로 `varchar(6) -> varchar(20)` migration을 baseline에 넣을 이유가 약하다.

왜냐하면:

- 현재 데이터는 6자 이내
- 실제 운영 장애를 만드는 mismatch가 아님
- baseline 목적은 existing DB 재현이지 미래 확장 반영이 아님

### 결정

- **baseline은 live DB `varchar(6)` 기준으로 간다**
- 이 항목은 baseline 후 별도 "symbol length standardization" 작업으로 다룬다

### 추천 후속 조치

선택지 A:
- `watchlist_item_orm.py` 를 `String(6)` 으로 되돌려 live schema와 맞춘다

선택지 B:
- 심볼 길이 표준을 프로젝트 전역에서 재설계한 뒤, 그때 `watchlist_items`를 widening migration 한다

안전 우선 기준 추천:
- **당장은 A 또는 보류**
- 즉시 widening은 권장하지 않음

### 실행 결과

2026-04-18 기준 `watchlist` 경로를 live schema 기준으로 정렬했다.

- `watchlist_item_orm.py`: `String(6)`
- `AddWatchlistRequest.symbol`: `max_length=6`
- live data 최대 길이: `6`

즉, 이 항목은 **watchlist 경로 기준 코드 정합화 완료** 상태다.
프로젝트 전역 symbol length standardization 여부는 별도 설계 과제로 남긴다.

---

## 4-2. `card_likes.uq_card_like_account`

### 현재 상태

- baseline 당시 live DB: `uq_card_like_ip` 만 존재
- ORM: `uq_card_like_ip` + `uq_card_like_account`

### 추가 확인

repository 로직:

- 로그인 사용자는 `liker_account_id` 기준으로 기존 좋아요를 조회
- `add_like()` 는 `IntegrityError` 발생 시 중복 좋아요로 간주하고 rollback

즉, 도메인 로직은 사실상 다음 규칙을 기대한다.

- 익명 사용자는 `(shared_card_id, liker_ip)` 유니크
- 로그인 사용자는 `(shared_card_id, liker_account_id)` 유니크

또한 live 데이터 확인 결과:

- `liker_account_id` 기준 중복 레코드는 현재 발견되지 않음

### 해석

이 항목은 baseline에서 바로 수정할 필요는 없지만, **장기적으로는 live DB가 ORM보다 약한 상태**다.

즉, 현재 운영 DB는 우연히 중복이 없을 뿐이고, race condition이나 동시 요청 상황에서는 중복 좋아요가 저장될 가능성이 있다.

### 결정

- **baseline은 live DB 기준으로 유지**
- **후속 revision에서 `uq_card_like_account` 추가 후 상태를 재검증한다**

### 추천 후속 조치

후속 revision 전에:

1. 중복 데이터 재검사
2. 중복이 있다면 정리 스크립트 준비
3. 그 다음 unique constraint 추가

즉, 이 항목은 **baseline 이후 정리 대상으로 분리된 drift**였다.

### 실행 결과

2026-04-18 기준 로컬 MySQL `multi_agent_db`에서 아래를 확인 후 실제 반영했다.

- `(shared_card_id, liker_account_id)` 기준 중복 레코드 없음
- non-null `liker_account_id` 레코드 수: `7`
- 적용 revision: `f84b02321df9`
- 반영 내용: `uq_card_like_account` unique constraint 추가

즉, 이 항목은 **로컬 기준 반영 완료 항목**이다.

---

## 4-3. `saved_articles.account_id` 인덱스

### 현재 상태

- live DB: `uq_saved_articles_account_link` unique 만 존재
- ORM: 여기에 더해 `account_id` 단독 index 기대

### 추가 확인

`saved_article_repository_impl.py` 기준 주요 쿼리:

- `find_by_link_and_account()`
- `find_all_by_account()`

즉, `account_id` 조건은 반복적으로 사용된다.

특히:

- 사용자 저장 기사 목록 조회
- 사용자별 중복 저장 체크

는 `account_id` 기반 접근이 핵심이다.

### 해석

이 인덱스는 없어도 기능은 동작한다.
하지만 데이터가 늘어날수록 `find_all_by_account()` 성능에 불리해진다.

따라서 이 항목은 구조/성능 상 ORM 쪽 의도가 더 타당하다.

다만 baseline 목적은 existing DB와의 일치이므로, 처음부터 여기에 index 추가를 섞지 않는 편이 안전하다.

### 결정

- **baseline은 live DB 기준**
- **후속 revision에서 `ix_saved_articles_account_id` 추가 권장**

### 추천 후속 조치

후속 migration 예:

```sql
CREATE INDEX ix_saved_articles_account_id ON saved_articles (account_id);
```

이건 비교적 저위험, 고효율 항목이라 baseline 직후 우선순위가 높다.

### 실행 결과

2026-04-18 기준 로컬 MySQL `multi_agent_db`에는 아래 revision을 통해 실제 반영했다.

- revision: `e86b70f9bed8`
- 내용: `saved_articles.account_id` 비고유 인덱스 추가

즉, 이 항목은 더 이상 "예정 drift"가 아니라 **로컬 기준 반영 완료 항목**이다.

---

## 4-4. `analysis_logs.source_type`

### 현재 상태

- live DB: `varchar(50)`
- ORM: `String(20)`

### 추가 확인

실제 저장된 값:

- `NEWS`
- `REPORT`
- `DISCLOSURE`
- `NULL`

실제 최대 길이:

- `10`

즉, 현재 데이터만 보면 `20`도 충분하다.

### 해석

하지만 이 mismatch는 성격이 다르다.

- `50 -> 20` 축소는 DDL 변경이 필요
- 현재 데이터가 짧다고 해도, business benefit은 크지 않다
- 더 넓은 길이 자체는 기능상 큰 문제를 만들지 않는다

따라서 이 항목은 baseline 이후에도 굳이 DB를 줄일 필요가 없을 수 있다.

### 결정

- **baseline은 live DB `varchar(50)` 기준**
- 추천은 **DB를 줄이기보다 ORM을 50으로 맞추는 방향**

### 추천 후속 조치

안전 우선 기준 추천:

- `analysis_log_orm.py` 의 `source_type` 길이를 `50`으로 맞춰 ORM을 live schema에 정합화

이게 가장 안전하고 변경 비용도 낮다.

### 실행 결과

2026-04-18 기준 `analysis_log_orm.py` 의 `source_type` 길이를 `String(50)` 으로 조정했다.

- live DB: `varchar(50)`
- ORM: `String(50)`

즉, 이 항목은 **DB migration 추가 없이 코드 정합화로 해소 완료** 상태다.

---

## 5. 최종 권장 전략

## baseline 단계

baseline 단계에서는 아래 원칙을 따른다.

- current live schema를 기준으로 initial revision을 수동 보정
- existing DB는 그 baseline revision에 `stamp`
- scratch/new DB는 `upgrade head`

즉, baseline은 "이상적인 미래 schema"가 아니라 **현재 운영 reality를 정확히 기록하는 revision**이어야 한다.

## baseline 직후 정리 우선순위

우선순위 추천:

1. `watchlist_items.symbol` 길이 표준 재설계

---

## 6. 다음 실제 작업 추천

현재 가장 안전한 다음 작업은 아래 둘 중 하나다.

### 추천 1. code-only 정합화 먼저 수행

DB를 안 건드리고 할 수 있는 저위험 정리:

- `watchlist_item_orm.py` 는 유지 또는 `6`으로 재정렬할지 별도 판단

### 추천 2. 제약조건 추가 전 데이터 점검

추가 제약/길이 변경이 필요한 항목은 바로 revision을 적용하기보다 먼저 데이터와 운영 정책을 점검해야 한다.

- 정책이 명확하면 Alembic revision 추가
- 데이터 정리가 필요하면 정리 정책 확정 후 migration 수행

안전 우선 기준에서 가장 추천하는 순서는:

1. `watchlist_items` 길이 정책 결정
2. 정책 확정 후 ORM 정합화 또는 schema revision 진행

---

## 7. 최종 판단

이번 drift 분석의 핵심 결론은 다음이다.

- **baseline은 live DB를 따라야 한다**
- **이상적인 ORM 목표 상태는 후속 revision으로 나눠야 한다**

즉, 지금 당장 해야 하는 것은 "ORM을 무조건 정답으로 밀어붙이는 것"이 아니다.

먼저:

- 운영 스키마를 baseline으로 고정하고
- stamp 가능한 상태를 만든 뒤
- 그 다음 drift를 하나씩 revision으로 제거하는 것이

가장 안전하고 재현 가능한 migration 전환 경로다.
