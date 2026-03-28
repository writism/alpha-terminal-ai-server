# BL-BE-19: YouTube 영상 댓글 수집

## 개요

시스템이 YouTube Data API를 사용하여 `youtube_videos` 테이블에 저장된 영상의 댓글을 수집한다.
수집된 댓글은 키워드 추출 단계에서 사용할 수 있는 형태로 반환된다.

## Success Criteria

- 시스템은 YouTube Data API `commentThreads`를 사용하여 특정 영상의 댓글을 조회한다
- 수집된 댓글에는 작성자명, 댓글 내용, 작성일, 좋아요 수가 포함된다
- 댓글이 비활성화된 영상이거나 댓글이 없는 경우 빈 리스트를 반환한다
- 시스템은 `youtube_videos` 테이블에 저장된 영상 ID (`video_id`)로 댓글 조회 요청을 생성한다
- 시스템은 댓글을 페이지 단위로 조회하며 최대 N개까지만 수집한다
- 시스템은 댓글을 최신순 또는 인기순 기준으로 정렬하여 수집한다
- 시스템은 댓글 내용이 비어있는 경우 해당 댓글을 제외한다
- 시스템은 동일한 댓글이 중복 수집되지 않도록 처리한다
- 유효하지 않은 영상 ID인 경우 댓글을 수집하지 않고 빈 리스트를 반환한다
- 수집된 댓글은 키워드 추출 단계에서 사용할 수 있는 형태로 반환된다

## To-do

- [x] YouTube Data API의 댓글 조회 기능을 External Client에 구현한다
- [x] 영상 ID (`video_id`)를 기반으로 댓글을 수집하는 UseCase를 구현한다
- [x] 댓글 수집 Response DTO를 정의한다
- [x] 댓글 조회 API 엔드포인트를 정의한다
- [x] 의존성 주입을 설정하고 라우터에 등록한다

## 기술 상세

- YouTube Data API v3 `commentThreads.list` 엔드포인트 사용
- `order` 파라미터: `relevance` (인기순) 또는 `time` (최신순)
- `maxResults`: 최대 100 (API 제한)
- 댓글 비활성화 영상은 API 403 응답 → 빈 리스트 반환
- comment_id 기반 중복 제거
