-- Migration: analysis_logs 테이블 컬럼 추가
-- Date: 2026-04-18
-- Reason: EC2 t4g.nano → t4g.small 업그레이드 후 MySQL 재시작 시
--         ORM 모델(AnalysisLogORM)과 실제 DB 스키마 불일치 발생.
--         article_published_at, source_name 컬럼이 DB에 누락되어 500 에러 발생.
--         url 컬럼은 이미 존재하여 제외.

ALTER TABLE analysis_logs
    ADD COLUMN article_published_at DATETIME NULL,
    ADD COLUMN source_name VARCHAR(100) NULL;
