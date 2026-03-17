# fixture 기반 정규화 로직 구현

작성자: 이승욱 (R2 정규화기)
작성일: 2026-03-17
관련 백로그: ADAIS-15

---

## 목적

`raw_article` fixture를 입력으로 받아 `normalized_article`을 생성하는 정규화 로직을 구현한다.

실제 수집기(R1) 없이도 fixture 데이터로 정규화 파이프라인을 테스트할 수 있다.

---

## 엔드포인트

```
POST /normalizer/articles
```

### Request (raw_article 필드 기반)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | str | O | raw_article UUID |
| `source_type` | str | O | `DISCLOSURE` \| `NEWS` \| `REPORT` |
| `source_name` | str | O | `DART`, `NAVER_NEWS` 등 |
| `title` | str | O | 원문 제목 |
| `body_text` | str | O | 원문 본문 |
| `published_at` | datetime | O | 발행 시각 (ISO 8601) |
| `symbol` | str | O | 종목 코드 (6자리) |
| `lang` | str | X | 언어 코드 (기본: `ko`) |

### Response (normalized_article 필드)

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | str | 정규화 결과 UUID (신규 생성) |
| `raw_article_id` | str | 입력 raw_article UUID |
| `stock_symbol` | str | 종목 코드 |
| `source_type` | str | 소스 타입 |
| `source_name` | str | 소스명 |
| `title` | str | 정제된 제목 |
| `body` | str | 정제된 본문 |
| `category` | str | 분류 결과 (enum) |
| `published_at` | datetime | KST 정규화된 발행 시각 |
| `lang` | str | 언어 코드 |
| `content_quality` | str | `VALID` \| `INVALID` |
| `normalized_at` | datetime | 정규화 처리 시각 (KST) |
| `normalizer_version` | str | `normalizer-v1.0.0` |

---

## 정규화 로직

### 제목/본문 정제 (`_clean_text`)

- 앞뒤 공백 제거 (`strip`)
- 연속 공백 단일 공백으로 치환 (`re.sub(r'\s+', ' ', ...)`)

### category 분류 (`_classify_category`)

| source_type | 조건 | category |
|-------------|------|----------|
| `NEWS` | - | `NEWS` |
| `REPORT` | - | `DISCLOSURE_OTHER` |
| `DISCLOSURE` | 제목에 `증자`, `전환사채`, `신주` 포함 | `DISCLOSURE_CAPITAL` |
| `DISCLOSURE` | 제목에 `실적`, `영업이익`, `매출` 포함 | `DISCLOSURE_EARNINGS` |
| `DISCLOSURE` | 그 외 | `DISCLOSURE_OTHER` |
| 기타 | - | `UNKNOWN` |

### content_quality 판단 (`_assess_quality`)

| 조건 | 결과 |
|------|------|
| 본문 없음 또는 10자 미만 | `INVALID` |
| 특수문자만으로 구성 | `INVALID` |
| 그 외 | `VALID` |

### published_at 정규화

- timezone 없는 경우 → KST(`+09:00`)로 간주
- timezone 있는 경우 → KST로 변환

---

## 구현 파일 목록

```
stock_normalizer/
├── domain/
│   ├── entity/
│   │   ├── normalized_article.py   ← NormalizedArticle, ArticleCategory, ContentQuality
│   │   └── raw_article.py          ← RawArticle (입력 표현)
│   └── service/
│       └── article_normalizer_service.py  ← 정제/분류/품질판단 핵심 로직
├── application/
│   ├── request/normalize_raw_article_request.py
│   ├── response/normalize_raw_article_response.py
│   └── usecase/
│       ├── normalized_article_repository_port.py
│       └── normalize_raw_article_usecase.py
└── adapter/
    ├── inbound/api/normalizer_router.py   ← POST /normalizer/articles
    └── outbound/persistence/normalized_article_repository_impl.py
```

---

## 검증 샘플

### DISCLOSURE (유상증자)

```json
// Request
{
  "id": "6ecab8bb-0d84-4bcf-bb2e-a5f2d6d4c8f1",
  "source_type": "DISCLOSURE",
  "source_name": "DART",
  "title": "삼성전자 유상증자 결정 공시",
  "body_text": "삼성전자는 운영자금 확보를 위해 보통주 1,000만 주에 대한 유상증자를 결정했다고 공시했다.",
  "published_at": "2026-03-15T08:30:00+09:00",
  "symbol": "005930",
  "lang": "ko"
}

// Response
{
  "category": "DISCLOSURE_CAPITAL",
  "content_quality": "VALID",
  "normalizer_version": "normalizer-v1.0.0"
}
```

### NEWS

```json
// Request
{
  "source_type": "NEWS",
  "source_name": "NAVER_NEWS",
  "title": "삼성전자, AI 반도체 투자 10조 원 확대…HBM4 양산 앞당긴다",
  ...
}

// Response
{
  "category": "NEWS",
  "content_quality": "VALID"
}
```

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 구현 및 문서 작성 |
