# Bruno API 컬렉션

## Bruno란?

[Bruno](https://www.usebruno.com/)는 Postman과 유사한 API 테스트 도구입니다.
**가장 큰 차이점은 컬렉션이 파일(`.yml`)로 저장된다는 점**으로, Git으로 버전 관리가 가능합니다.

| | Bruno | Postman |
|---|---|---|
| 저장 방식 | 로컬 파일 (`.yml`) | 클라우드 |
| Git 관리 | 가능 | 별도 설정 필요 |
| 무료 여부 | 완전 무료 | 일부 유료 |

---

## 설치

```bash
brew install bruno
```

또는 [공식 사이트](https://www.usebruno.com/downloads)에서 다운로드

---

## 컬렉션 열기

1. Bruno 실행
2. 좌측 상단 **Collections** → `...` → **Open Collection**
3. 이 폴더(`docs/bruno/`) 선택

---

## Postman 사용자라면

Bruno `.yml` 파일은 Postman에서 직접 사용할 수 없습니다.
같은 폴더에 있는 **`alpha-desk.postman_collection.json`** 을 대신 사용하세요.

**가져오기 방법:**
1. Postman 실행
2. **Import** 버튼 클릭
3. `alpha-desk.postman_collection.json` 파일 선택

---

## API 목록

서버 기본 URL: `http://localhost:33333`

### 1. 뉴스 검색 — `GET /news/search`

구글 뉴스에서 키워드로 기사를 검색합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `keyword` | string | Y | 검색 키워드 |
| `page` | integer | N | 페이지 번호 (기본값: 1) |
| `size` | integer | N | 페이지 크기 (기본값: 10) |

```
GET /news/search?keyword=google&page=1&size=10
```

---

### 2. 기사 저장 — `POST /news/saved`

기사를 DB에 저장합니다. 링크를 기준으로 중복 저장을 방지하며, 본문은 자동으로 크롤링됩니다.

**Request Body:**
```json
{
  "title": "기사 제목",
  "link": "https://example.com/article",
  "source": "출처 (선택)",
  "snippet": "요약 텍스트 (선택)",
  "published_at": "발행일 (선택)"
}
```

- 이미 저장된 링크이면 `409 Conflict` 반환

---

### 3. 기사 분석 — `GET /news/saved/{article_id}/analysis`

저장된 기사를 AI로 분석하여 감성 분석과 키워드를 반환합니다.

```
GET /news/saved/1/analysis
```

**Response:**
```json
{
  "article_id": 1,
  "keywords": ["키워드1", "키워드2"],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.85
}
```

| sentiment 값 | 의미 |
|---|---|
| `POSITIVE` | 긍정 |
| `NEGATIVE` | 부정 |
| `NEUTRAL` | 중립 |

- 기사가 없거나 본문이 비어있으면 `422 Unprocessable Entity` 반환
