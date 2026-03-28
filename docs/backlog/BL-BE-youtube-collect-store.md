# BL-BE-youtube-collect-store 시스템이 수집된 관심종목 관련 영상 데이터를 데이터베이스에 저장한다

## Backlog Type
Behavior Backlog

## 배경
사전 정의된 뉴스 채널에서 관심종목 관련 YouTube 영상을 수집하고,
중복 검증 후 데이터베이스에 저장/갱신하여 영상 피드 페이지에 제공한다.

## 도메인
youtube

## 검색 대상 채널
- UCF8AeLlUbEpKju6v1H6p8Eg (한국경제TV)
- UCbMjg2EvXs_RUGW-KrdM3pw (SBS Biz)
- UCTHCOPwqNfZ0uiKOvFyhGwg (연합뉴스TV)
- UCcQTRi69dsVYHN3exePtZ1A (KBS News)
- UCG9aFJTZ-lMCHAiO1KJsirg (MBN)
- UCsU-I-vHLiaMfV_ceaYz5rQ (JTBC News)
- UClErHbdZKUnD1NyIUeQWvuQ (머니투데이)
- UC8Sv6O3Ux8ePVqorx8aOBMg (이데일리TV)
- UCnfwIKyFYRuqZzzKBDt6JOA (매일경제TV)

## Success Criteria

- 시스템은 사전 정의된 9개 채널만 조회하여 비관련 콘텐츠 유입을 방지한다
- 시스템은 각 채널의 최근 N일 이내 영상만 조회한다
- 시스템은 사용자 관심종목 키워드로 영상을 필터링한다
- 시스템은 영상 목록을 게시일 기준 정렬 후 상위 10개를 선택한다
- 시스템은 videoId 기준 중복 검증 후 신규 저장 / 기존 갱신한다
- 영상 ID, 제목, 채널명, 게시일, 조회수, 썸네일 URL, 영상 URL을 저장한다
- 저장 완료된 영상만 최종 결과로 반환된다
- 저장 대상이 없으면 DB 변경 없이 빈 리스트를 반환한다
- 저장 오류 시 해당 영상은 저장되지 않는다

## Todo

1. 영상 데이터를 저장할 수 있는 구조를 정의한다
2. 영상 ID 기준 중복 검증 로직을 구현한다
3. 기존 데이터 갱신 로직을 구현한다
4. 필터링된 영상 데이터를 저장하는 기능을 구현한다
5. 저장된 데이터 기반으로 결과를 반환하도록 수정한다

## 상태
- [ ] 구현 전
