# BL-BE-85: SerpClient._shared_client lifespan 종료 훅 추가

## 문제

`SerpClient._shared_client` (httpx.Client) 가 프로세스 종료 시 명시적으로 닫히지 않는다.

- OS 가 정리하지만 FastAPI `lifespan` 수명 주기와 불일치
- 테스트 간 클래스 레벨 싱글턴이 공유되어 격리 어려움
- 운영 환경에서 graceful shutdown 시 커넥션 leak 가능성

## 해결 방안

1. `SerpClient` 에 `@classmethod close()` 추가 — `_shared_client.close()` 후 `None` 초기화
2. `main.py` lifespan `yield` 이후 shutdown 블록에서 `SerpClient.close()` 호출

## 범위

- `app/infrastructure/external/serp_client.py`
- `main.py`

## 완료 기준

- 앱 종료 시 httpx.Client 가 lifespan shutdown 에서 닫힘
- 테스트에서 픽스처로 `SerpClient.close()` 호출 가능
