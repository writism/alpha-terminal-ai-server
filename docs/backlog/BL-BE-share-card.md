# BL-BE-share-card

**Backlog Type**
Feature

**Backlog Title**
AI 분석 카드 공유 — 백엔드 (공유 카드 CRUD · 좋아요 · 댓글)

---

## 1. 배경

사용자가 대시보드의 AI 분석 카드를 공유하면,
공유된 카드는 홈 피드에 노출되고 다른 사용자(익명 포함)가 좋아요 · 댓글을 달 수 있다.
공유 링크를 SNS에 올리면 카드 내용이 OG 메타태그로 미리보기된다.

---

## 2. DB 설계

### shared_cards

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT PK | |
| symbol | VARCHAR(20) | 종목 심볼 |
| name | VARCHAR(100) | 종목명 |
| summary | TEXT | AI 요약 |
| tags | JSON | 태그 배열 |
| sentiment | VARCHAR(20) | POSITIVE/NEGATIVE/NEUTRAL |
| sentiment_score | FLOAT | -1.0 ~ 1.0 |
| confidence | FLOAT | 0.0 ~ 1.0 |
| source_type | VARCHAR(20) | NEWS/DISCLOSURE/REPORT |
| url | VARCHAR(500) | 원문 URL (nullable) |
| analyzed_at | DATETIME | AI 분석 시각 |
| sharer_account_id | INT | 공유자 account_id (nullable) |
| sharer_nickname | VARCHAR(100) | 공유자 닉네임 (denormalized) |
| like_count | INT | 좋아요 수 (default 0) |
| comment_count | INT | 댓글 수 (default 0) |
| created_at | DATETIME | 공유 시각 |

### card_likes

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT PK | |
| shared_card_id | INT FK | |
| liker_ip | VARCHAR(45) | 익명 식별용 IP |
| liker_account_id | INT | 로그인 사용자 (nullable) |
| created_at | DATETIME | |

- UNIQUE(shared_card_id, liker_ip): 동일 IP 중복 좋아요 방지

### card_comments

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT PK | |
| shared_card_id | INT FK | |
| content | VARCHAR(120) | 댓글 본문 (120자 제한) |
| author_nickname | VARCHAR(100) | 작성자 닉네임 (nullable → '익명') |
| author_account_id | INT | 로그인 사용자 (nullable) |
| author_ip | VARCHAR(45) | 익명 식별용 IP |
| created_at | DATETIME | |

---

## 3. API 설계

### 공유 카드

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| POST | /card-share | 로그인 필요 | 카드 공유 |
| GET | /card-share | 불필요 | 공유 카드 목록 (홈 피드) |
| GET | /card-share/{card_id} | 불필요 | 단일 카드 (SNS 링크용) |
| DELETE | /card-share/{card_id} | 본인만 | 공유 취소 |

### 좋아요

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| POST | /card-share/{card_id}/likes | 불필요 | 좋아요 토글 (IP 기반) |

### 댓글

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| GET | /card-share/{card_id}/comments | 불필요 | 댓글 목록 |
| POST | /card-share/{card_id}/comments | 불필요 | 댓글 작성 |

---

## 4. Request / Response DTO

### POST /card-share (Request)
```json
{
  "symbol": "234340",
  "name": "헥토파이낸셜",
  "summary": "유진증권이...",
  "tags": ["실적", "산업동향"],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.7,
  "confidence": 0.8,
  "source_type": "NEWS",
  "url": "https://...",
  "analyzed_at": "2026-03-26T12:00:00"
}
```

### GET /card-share (Response)
```json
{
  "cards": [
    {
      "id": 1,
      "symbol": "234340",
      "name": "헥토파이낸셜",
      "summary": "...",
      "tags": ["실적"],
      "sentiment": "POSITIVE",
      "sentiment_score": 0.7,
      "confidence": 0.8,
      "source_type": "NEWS",
      "analyzed_at": "2026-03-26T12:00:00",
      "sharer_nickname": "btdlm",
      "like_count": 5,
      "comment_count": 2,
      "created_at": "2026-03-26T20:00:00"
    }
  ],
  "total": 10
}
```

### POST /card-share/{card_id}/likes (Response)
```json
{ "liked": true, "like_count": 6 }
```

### POST /card-share/{card_id}/comments (Request)
```json
{
  "content": "좋은 분석이네요! (120자 이내)",
  "author_nickname": "익명사용자"
}
```

---

## 5. 아키텍처 구조 (Hexagonal)

```
domains/card_share/
  domain/entity/
    shared_card.py
    card_like.py
    card_comment.py
  application/
    usecase/
      share_card_usecase.py
      toggle_like_usecase.py
      add_comment_usecase.py
      get_shared_cards_usecase.py
    request/
      share_card_request.py
      add_comment_request.py
    response/
      shared_card_response.py
      card_comment_response.py
  adapter/
    inbound/api/
      card_share_router.py
    outbound/persistence/
      card_share_repository_impl.py
  infrastructure/
    orm/
      shared_card_orm.py
      card_like_orm.py
      card_comment_orm.py
    mapper/
      card_share_mapper.py
```

---

## 6. Success Criteria

| ID | 기준 |
|----|------|
| SC-1 | POST /card-share → 카드 저장, 200 반환 |
| SC-2 | GET /card-share → 최신순 카드 목록 반환 |
| SC-3 | GET /card-share/{id} → 단일 카드 반환 |
| SC-4 | POST /likes → 좋아요 토글, like_count 증감 |
| SC-5 | 동일 IP 중복 좋아요 불가 |
| SC-6 | POST /comments → 댓글 저장, 120자 초과 시 400 반환 |
| SC-7 | author_nickname 미입력 시 '익명' 기본값 적용 |

---

## 7. 완료 정의

- [ ] SC-1 ~ SC-7 통과
- [ ] main.py에 card_share_router 등록
- [ ] ORM 자동 생성 확인
