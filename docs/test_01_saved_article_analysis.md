# 저장된 뉴스 기사 AI 분석

작성자: 이승욱
작성일: 2026-03-18
관련 백로그: ADAIS-24

---

## Backlog Title

R3 AI 처리기가 저장된 뉴스 기사의 키워드와 감정을 분석한다

---

## Success Criteria

- 저장된 뉴스 기사(saved_article)를 ID로 조회할 수 있다
- 기사 본문을 OpenAI gpt-5-mini로 분석하여 키워드와 감정을 반환한다
- `GET /news/saved/{article_id}/analysis` API가 동작한다
- 키워드는 최대 5개, 한글 키워드로 반환된다
- sentiment: POSITIVE | NEGATIVE | NEUTRAL + sentiment_score 반환

---

## Todo

- [x] SavedArticleRepositoryPort에 find_by_id() 추가
- [x] ArticleAnalysis 도메인 엔티티 정의
- [x] ArticleAnalysisPort (ABC) 정의
- [x] AnalyzeArticleUseCase 구현
- [x] OpenAIAnalysisAdapter 구현 (gpt-5-mini Responses API)
- [x] GET /news/saved/{article_id}/analysis 엔드포인트 추가

---

## 구현 파일 목록 (테스트 백로그 — 미커밋 상태)

```
app/domains/news_search/
├── domain/entity/article_analysis.py           ← ArticleAnalysis dataclass
├── application/usecase/article_analysis_port.py ← ABC Port
├── application/usecase/analyze_article_usecase.py
├── application/usecase/saved_article_repository_port.py  ← find_by_id() 추가
├── adapter/inbound/api/saved_article_router.py ← GET /news/saved/{id}/analysis 추가
└── adapter/outbound/external/openai_analysis_adapter.py
```

## API 엔드포인트

```
GET /news/saved/{article_id}/analysis
```

### Response 예시

```json
{
  "article_id": 4,
  "keywords": ["AI 메모리", "HBM4·HBM3E", "eSSD", "NVIDIA 협업", "GTC 2026"],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.8
}
```

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-18 | 이승욱 | 최초 작성 (테스트 백로그 기반) |
