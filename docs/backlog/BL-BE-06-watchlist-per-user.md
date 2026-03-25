# BL-BE-06

**Backlog Type**
Behavior Backlog

**Backlog Title**
시스템이 관심종목을 로그인한 사용자별로 분리하여 관리한다

**Status**
완료 (2026-03-23)

**배경**
기존 watchlist_items 테이블에 account_id 컬럼이 없어 모든 사용자가 동일한 관심종목을 공유하였다.
사용자별로 관심종목을 분리하고, 자신의 관심종목만 조회/추가/삭제할 수 있어야 한다.
account_id는 로그인 시 설정되는 account_id 쿠키에서 추출한다.

**Success Criteria**
- 관심종목 추가 시 account_id가 함께 저장된다
- 관심종목 조회 시 로그인한 사용자의 관심종목만 반환된다
- 동일 종목을 서로 다른 사용자가 각각 등록할 수 있다
- 파이프라인 실행 시 로그인한 사용자의 관심종목을 기준으로 분석한다

**Todo**
1. [x] WatchlistItemORM에 account_id 컬럼 및 (account_id, symbol) 복합 unique 제약을 추가한다
2. [x] WatchlistItem 엔티티에 account_id 필드를 추가한다
3. [x] WatchlistItemMapper에 account_id 매핑을 추가한다
4. [x] WatchlistRepositoryPort/Impl의 find_all, find_by_symbol에 account_id 파라미터를 추가한다
5. [x] AddWatchlistUseCase, GetWatchlistUseCase에 account_id 파라미터를 추가한다
6. [x] watchlist_router에서 account_id 쿠키를 추출하여 UseCase에 전달한다
7. [x] RunPipelineUseCase.execute()에 account_id 파라미터를 추가하여 watchlist 조회에 전달한다
8. [x] pipeline_router에서 account_id 쿠키를 추출하여 RunPipelineUseCase에 전달한다

**DB 마이그레이션**

대상 테이블: `watchlist_items`

```sql
-- 1. account_id 컬럼 추가
ALTER TABLE watchlist_items ADD COLUMN account_id INT NULL;

-- 2. 기존 symbol 단독 unique index 제거
ALTER TABLE watchlist_items DROP INDEX symbol;

-- 3. (account_id, symbol) 복합 unique constraint 추가
ALTER TABLE watchlist_items ADD UNIQUE KEY uq_watchlist_account_symbol (account_id, symbol);
```

실행일: 2026-03-23
실행 결과: 성공

**변경된 파일**
- `app/domains/watchlist/infrastructure/orm/watchlist_item_orm.py`
- `app/domains/watchlist/domain/entity/watchlist_item.py`
- `app/domains/watchlist/infrastructure/mapper/watchlist_item_mapper.py`
- `app/domains/watchlist/application/usecase/watchlist_repository_port.py`
- `app/domains/watchlist/adapter/outbound/persistence/watchlist_repository_impl.py`
- `app/domains/watchlist/application/usecase/add_watchlist_usecase.py`
- `app/domains/watchlist/application/usecase/get_watchlist_usecase.py`
- `app/domains/watchlist/adapter/inbound/api/watchlist_router.py`
- `app/domains/pipeline/application/usecase/run_pipeline_usecase.py`
- `app/domains/pipeline/adapter/inbound/api/pipeline_router.py`
