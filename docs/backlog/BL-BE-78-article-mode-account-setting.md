# BL-BE-78: article_mode 계정 설정 저장 + 스케줄러 연동

## 문제
- 스케줄러(`run_pipeline_job`)가 `ArticleMode.LATEST_3` 하드코딩
- 사용자별 article_mode 설정이 서버에 저장되지 않음
- 자동 실행 파이프라인이 My Page 설정을 무시하고 항상 기본값으로 실행됨

## 목표
- `accounts` 테이블에 `article_mode` 컬럼 추가
- Account Settings API (GET/PATCH)에 `article_mode` 포함
- 스케줄러가 계정별 `article_mode` 읽어 실행

## 구현 범위

### BE
- `AccountORM`: `article_mode` 컬럼 추가 (String, default="latest_3")
- Alembic migration 추가
- `UpdateSettingsRequest`, `AccountSettingsResponse`에 `article_mode` 추가
- `run_pipeline_job`: account_id=None이면 전체 계정을 순회하며 각자 설정 적용

### FE (BL-FE-76 연동)
- `updateArticleMode` 시 서버 PATCH 호출
- 앱 로드 시 서버에서 article_mode 읽기 (localStorage 대신 or 병행)

## 선행 조건
- BL-FE-75 (localStorage 영속화) 완료 후 진행 권장
- 운영 DB 백업 후 migration 적용

## 완료 기준
- 스케줄러 실행 로그에 계정별 article_mode가 찍힘
- My Page에서 설정 변경 후 다음 자동 실행에 반영됨
