# 검색 결과 일괄 AI 분석

작성자: 이승욱
작성일: 2026-03-18
관련: TEST-06 (로컬 전용 — 커밋/푸시 금지)

---

## Backlog Title

시스템이 뉴스 검색 결과를 일괄 저장하고 AI 분석 결과를 반환한다

---

## Success Criteria

- `POST /news/bulk-analysis` 엔드포인트로 검색어를 입력하면 검색 → 저장 → 분석이 한 번에 처리된다
- 검색된 기사를 순서대로 저장하고, 각 기사에 대해 키워드·감정 분석을 수행한다
- 이미 저장된 기사(동일 링크)는 중복 저장하지 않고 기존 ID로 분석한다
- 기사 본문이 없거나 분석 실패한 기사는 건너뛰고 나머지 결과를 반환한다
- 응답은 분석된 기사 목록(title, keywords, sentiment, sentiment_score)을 배열로 반환한다

---

## Todo

- [ ] BulkAnalyzeRequest / BulkAnalyzeResponse DTO 정의
- [ ] BulkAnalyzeUseCase 구현 (검색 → 저장 → 분석 파이프라인)
- [ ] POST /news/bulk-analysis 엔드포인트 추가

---

## API 엔드포인트

```
POST /news/bulk-analysis
```

### Request

```json
{
  "query": "NHN KCP",
  "page_size": 10
}
```

### Response 예시

```json
{
  "query": "NHN KCP",
  "total": 8,
  "results": [
    {
      "article_id": 7,
      "title": "NHN KCP Signs MOU to Link PayPay Network",
      "sentiment": "POSITIVE",
      "sentiment_score": 0.8,
      "keywords": ["NHN KCP", "PayPay", "SBPS", "KOTRA", "역직구"]
    }
  ]
}
```

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-18 | 이승욱 | 최초 작성 및 구현 |
