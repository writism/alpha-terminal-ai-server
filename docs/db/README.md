# DB 설정 가이드

이 디렉토리는 로컬 MySQL Docker 환경 설정과 Alembic 마이그레이션 관련 파일을 포함한다.

## 파일 목록

| 파일 | 설명 |
|------|------|
| `docker-compose.yml` | MySQL Docker 설정 (팀 공통) |
| `alembic-guide.md` | Alembic 개념 및 사용법 설명 |
| `env.py` | `alembic init` 후 `alembic/env.py`에 덮어쓸 완성본 |
| `alembic.ini.example` | `alembic.ini` 예시 |

---

## 팀원 온보딩 순서

처음 세팅하는 경우 아래 순서대로 진행한다.

```bash
# 1. 저장소 클론
git clone <repo-url>
cd alpha-desk-ai-server

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일에서 DB 접속 정보 채우기

# 4. MySQL Docker 시작
docker-compose up -d

# 5. Alembic 스키마 적용
alembic upgrade head

# 6. 서버 시작
uvicorn main:app --reload --host 0.0.0.0 --port 33333
```

---

## 스키마 변경 시 워크플로우

```bash
# ORM 파일 수정 후
alembic revision --autogenerate -m "변경 내용 요약"

# 생성된 파일 확인 후 git 커밋
git add alembic/versions/
git commit -m "migration: 변경 내용"
git push
```

팀원들은 `git pull` 후 `alembic upgrade head` 한 번이면 동기화 완료.
