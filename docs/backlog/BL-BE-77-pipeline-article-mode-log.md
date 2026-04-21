# BL-BE-77: 파이프라인 article_mode + 종목별 기사 건수 로그

## 문제
- 파이프라인 실행 시 `article_mode`가 어떤 값으로 실행되는지 서버 로그에 남지 않음
- 종목별로 뉴스/공시가 몇 건 선택되어 stock_analyzer에 전달되는지 확인 불가
- My Page 설정이 실제로 반영되는지 로그로 검증할 방법 없음

## 목표
- `execute()` 시작 시 `article_mode` 값 로그 출력
- 종목별 수집 후 선택 건수(뉴스/공시) 로그 출력
- `_analyze_articles()` 진입 시 stock_analyzer 입력 건수 로그 출력

## 구현 위치
- `app/domains/pipeline/application/usecase/run_pipeline_usecase.py`

## 완료 기준
- 파이프라인 실행 로그에서 article_mode + 종목별 선택 건수 확인 가능
