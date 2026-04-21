# Alpha-Desk 2.0 MVP 구현 현황

> 기준일: 2026-04-13

---

## 전체 요약

| 단계 | 목표 | BE 상태 | FE 상태 |
|------|------|---------|---------|
| 0단계 | 용어 설명 | ✅ 완료 | ❌ 미구현 |
| 1단계 | 데이터 축적 | ⚠️ 일부 완료 | ❌ 미구현 |
| 2단계 | 지능형 필터링 | ✅ 완료 (Mock) | ❌ 미구현 |
| 3단계 | 능동형 추천 | ❌ 미구현 | ❌ 미구현 |

---

## 0단계 — 용어 설명 기능 (Week 1)

> 어려운 주식 용어를 AI가 쉽게 설명해주는 기능

| 담당 | 작업 내용 | 상태 | 비고 |
|------|-----------|------|------|
| 김동녁 | BE `POST /market-analysis/explain-term` API | ✅ 완료 | `market_analysis_router.py` |
| 김동녁 | BE LangChain 기반 용어 설명 체인 | ✅ 완료 | `langchain_term_explainer_adapter.py` |
| 김동녁 | BE 금융 용어 사전 데이터 구축 | ✅ 완료 | LangChain 프롬프트 내 내장 |
| 김동녁 | FE 용어 클릭 시 설명 팝업 UI | ❌ 미구현 | API 연동 없음 |

---

## 1단계 — 데이터 축적 (Week 1~2)

> 사용자 상호작용 데이터를 AI가 이해하는 형식으로 저장

| 담당 | 작업 내용 | 상태 | 비고 |
|------|-----------|------|------|
| 김동녁 | `user_profile` 도메인 설계 + 헥사고날 구조 세팅 | ✅ 완료 | ORM/Mapper/Port/UseCase 모두 존재 |
| 최승호 | BE `GET /users/{user_id}/profile` API | ❌ 미구현 | 라우터 파일 없음, main.py 미등록 |
| 최승호 | FE `/profile` 페이지 | ❌ 미구현 | 라우트 없음 |
| 이하연 | BE 자정 배치 프로필 자동 업데이트 스케줄러 | ❌ 미구현 | Pipeline 스케줄러만 존재 |

---

## 2단계 — 지능형 필터링 (Week 2~3)

> AI가 요약 전에 사용자 취향을 먼저 조회해서 맞춤형 분석 제공

| 담당 | 작업 내용 | 상태 | 비고 |
|------|-----------|------|------|
| 이승욱 | BE `market_analysis` 체인에 `get_user_profile` Tool 추가 | ✅ 완료 | `get_user_profile_tool.py` |
| 이승욱 | BE 사용자 취향 기반 맞춤 프롬프트 개선 | ✅ 완료 | `context_builder_service.py` |
| 이승욱 | FE 분석 결과 카드에 개인화 태그 표시 | ⚠️ 부분 완료 | Stock Picks 카드에만 `PERSONALIZED` 뱃지 구현, Dashboard/저장기사 카드는 미적용 |

> ⚠️ `get_user_profile` Tool이 실 DB 대신 **Mock 데이터** 사용 중
> → 1단계 `GET /users/{user_id}/profile` API 완성 후 실 데이터로 교체 필요

---

## 3단계 — 능동형 추천 (Week 3~4)

> 사용자가 앱을 켜지 않아도 AI가 관심 종목 이슈를 먼저 감지해서 알림 전송

| 담당 | 작업 내용 | 상태 | 비고 |
|------|-----------|------|------|
| 김동녁 | BE `agent_proactive_recommendation` 도메인 | ❌ 미구현 | — |
| 김동녁 | BE 백그라운드 에이전트 스케줄러 | ❌ 미구현 | — |
| 김민식 | BE 알림 서비스 (`notifications` 테이블 + CRUD API) | ❌ 미구현 | — |
| 김민식 | FE 헤더 알림 아이콘 + 뱃지 + 드롭다운 + 토스트 팝업 | ❌ 미구현 | — |

---

## 기존 완성 기능

| 기능 | BE | FE |
|------|----|----|
| 카카오 OAuth 로그인/로그아웃 | ✅ | ✅ |
| 관심종목 (Watchlist) CRUD | ✅ | ✅ |
| 뉴스 검색 (KR/US 분리, Naver+SERP+Finnhub) | ✅ | ✅ |
| 뉴스 필터 (마켓/제목/날짜 정렬) | ✅ | ✅ |
| 기사 저장 + trafilatura 본문 크롤링 | ✅ | ✅ |
| 저장 기사 AI 감성 분석 + 키워드 | ✅ | ✅ |
| 대시보드 + 분석 파이프라인 | ✅ | ✅ |
| 모바일 반응형 UI + 하단 네비게이션 | — | ✅ |
| CI/CD (GitHub Actions → GHCR → EC2) | ✅ | — |
| Redis 세션/캐시 | ✅ | — |
| PostgreSQL JSONB 비정형 데이터 저장 | ✅ | — |

---

## 인프라 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| AWS EC2 배포 | ✅ 운영 중 | 13.209.48.158, self-hosted runner |
| GitHub Actions CI/CD | ✅ 운영 중 | main push → 자동 빌드·배포 |
| MySQL (RDS) | ✅ 운영 중 | 메타데이터 저장 |
| PostgreSQL | ✅ 운영 중 | JSONB 비정형 데이터 |
| Redis | ✅ 운영 중 | 세션, 토큰 캐시 |
| pgvector | ❌ 미설치 | 벡터 DB 결정 필요 |
| FCM / Web Push | ❌ 미구현 | 알림 방식 결정 필요 |

---

## 미결 사항

- [ ] Vector DB 결정 (pgvector vs Chroma)
- [ ] 알림 방식 결정 (FCM vs Web Push)
- [ ] 담당자별 미완성 태스크 완료 일정 조율
