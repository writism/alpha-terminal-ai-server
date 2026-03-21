# Alembic 마이그레이션 가이드

## 왜 필요한가

현재 `main.py`에 `Base.metadata.create_all(bind=engine)` 이 있다.

- 테이블이 없으면 생성 ✅
- **이미 있는 테이블에 컬럼 추가/변경 → 반영 안 됨** ❌

팀원마다 Docker MySQL 로컬 DB를 따로 돌리는 환경에서, ORM 모델이 바뀌면 각자의 DB 스키마가 달라진다.
Alembic은 스키마 변경 내역을 **파일로 git 커밋**해서 공유하는 버전 관리 도구다.

---

## 개념

```
개발자 A — ORM 모델 수정
         → alembic revision --autogenerate  (변경 감지해서 파일 생성)
         → git push

팀원 B   → git pull
         → alembic upgrade head             (파일 읽어서 내 DB에 자동 적용)
```

git에 커밋되는 파일: `alembic/versions/*.py`

---

## 최초 설정 요약 (한 번만)

```bash
alembic init alembic                                      # 1. alembic 디렉토리 생성
cp docs/db/env.py alembic/env.py                          # 2. 이 프로젝트용 env.py 적용
alembic revision --autogenerate -m "initial schema"       # 3. 현재 ORM → 마이그레이션 파일 생성
alembic upgrade head                                      # 4. 내 DB에 스키마 적용
# main.py 에서 Base.metadata.create_all(bind=engine) 제거 # 5. create_all 제거
```

각 단계 상세 설명은 아래 참고.

---

## 최초 설정 상세 (한 번만)

### 1. 설치

```bash
pip install alembic
# requirements.txt에 추가: alembic>=1.13.0
```

### 2. 초기화

```bash
cd alpha-desk-ai-server
alembic init alembic
```

생성되는 구조:
```
alembic/
├── env.py          ← 핵심 설정 파일 (docs/db/env.py로 덮어쓸 것)
├── script.py.mako  ← 마이그레이션 파일 템플릿
└── versions/       ← 마이그레이션 파일들 (git 관리 대상)
alembic.ini         ← alembic 설정 (docs/db/alembic.ini.example 참고)
```

### 3. env.py 교체

`docs/db/env.py`를 `alembic/env.py`에 덮어쓴다.

```bash
cp docs/db/env.py alembic/env.py
```

이 파일이 하는 일:
- `.env` 파일에서 DB 접속 정보 읽기
- 모든 ORM 모델 import (autogenerate 비교 기준)

> **주의**: 새 도메인 ORM 파일 추가 시 `alembic/env.py` import 목록에도 반드시 추가

### 4. 초기 마이그레이션 생성

현재 ORM 모델 전체를 "버전 0"으로 찍는다.

```bash
alembic revision --autogenerate -m "initial schema"
```

`alembic/versions/xxxx_initial_schema.py` 생성 확인 후 내용을 검토한다.

### 5. DB에 적용

```bash
alembic upgrade head
```

### 6. main.py 수정

`create_all()`과 Alembic이 공존하면 충돌할 수 있으므로 제거한다.

```python
# main.py — 아래 줄 삭제
Base.metadata.create_all(bind=engine)
```

---

## 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `alembic upgrade head` | 내 DB를 최신 버전으로 올리기 |
| `alembic revision --autogenerate -m "설명"` | ORM 변경 감지해서 마이그레이션 파일 생성 |
| `alembic current` | 현재 내 DB 버전 확인 |
| `alembic history` | 마이그레이션 이력 전체 조회 |
| `alembic downgrade -1` | 한 버전 롤백 |
| `alembic downgrade base` | 모든 마이그레이션 롤백 (초기화) |

---

## 스키마 변경 워크플로우

### ORM 컬럼 추가 예시

```python
# watchlist_item_orm.py 수정
class WatchlistItemORM(Base):
    __tablename__ = "watchlist_items"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(6))
    account_id = Column(Integer, nullable=True)  # ← 추가
```

```bash
alembic revision --autogenerate -m "add account_id to watchlist_items"
# 생성된 파일 확인
git add alembic/versions/
git commit -m "migration: add account_id to watchlist_items"
git push
```

팀원:
```bash
git pull
alembic upgrade head
```

---

## 새 도메인 ORM 추가 시

ORM 파일을 새로 만들면 `alembic/env.py`에 import를 추가해야 autogenerate가 감지한다.

```python
# alembic/env.py
from app.domains.new_domain.infrastructure.orm.new_orm import NewORM  # noqa: F401
```

---

## 주의사항

| 상황 | 조치 |
|------|------|
| autogenerate가 변경을 감지 못함 | ORM import 누락 확인. 일부 변경(인덱스명 등)은 수동 작성 필요 |
| 마이그레이션 파일 충돌 | `alembic heads`로 확인 → `alembic merge heads` 로 병합 |
| DB 완전 초기화 | `alembic downgrade base` → `alembic upgrade head` |
| 생성된 파일을 수정해도 됨 | autogenerate는 초안. 검토 후 필요하면 직접 편집 가능 |
