# BL-BE-20: YouTube 댓글 명사 추출

## 개요

시스템이 `video_comments` 테이블에 저장된 댓글 텍스트에서 한국어 명사를 추출하고 빈도수 기준으로 정렬하여 반환한다.

## 전제 조건

- BL-BE-19에서 수집한 댓글을 `video_comments` 테이블에 저장하는 기능 추가 필요
- 한국어 형태소 분석 라이브러리 `kiwipiepy` 설치

## Success Criteria

- 시스템은 `video_comments` 테이블에 저장된 댓글 텍스트를 대상으로 명사를 추출한다
- 시스템은 한국어 형태소 분석기(kiwipiepy)를 사용하여 명사만 분리한다
- 추출된 명사는 빈도수 기준으로 정렬되어 반환된다

## To-do

- [x] 댓글 저장용 `video_comments` 테이블 ORM + Repository 구현
- [x] 댓글 수집 시 DB에 upsert 저장 로직 추가
- [x] `kiwipiepy` 설치 및 Infrastructure에 형태소 분석 어댑터 구성
- [x] DB에 저장된 댓글 텍스트에서 명사를 추출하는 UseCase 구현
- [x] 명사 빈도수 Response DTO 정의
- [x] 명사 추출 API 엔드포인트를 정의하고 라우터에 등록
