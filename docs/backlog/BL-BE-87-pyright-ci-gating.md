# BL-BE-87: pyright CI 실질 게이팅 (continue-on-error 제거 + pip 캐시)

## 문제

`.github/workflows/main.yml` 의 `typecheck` 잡이 `continue-on-error: true` 로 설정되어
pyright 오류가 있어도 CI 가 통과된다. 사실상 결과를 수집만 하는 배지 수준이다.

추가로 `pip install -r requirements.txt` 가 매 실행마다 캐시 없이 실행된다.

## 해결 방안

1. `continue-on-error: true` 제거 → pyright 실패 시 CI fail
2. `actions/cache` 또는 `setup-python` 의 `cache: pip` 로 의존성 캐싱

## 범위

- `.github/workflows/main.yml`

## 완료 기준

- pyright 오류 발생 시 CI 가 fail (빨간불)
- pip install 단계 캐시로 빌드 시간 단축
