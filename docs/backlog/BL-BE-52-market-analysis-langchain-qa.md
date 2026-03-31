# BL-BE-52

**Backlog Type**
Feature / market_analysis + LangChain

**Backlog Title**
관심종목 컨텍스트 기반 LangChain Q&A — 키워드·테마 주입 질문 분석

**Success Criteria**
- Domain 패키지는 `market_analysis`로 구성한다.
- 시스템은 LangChain 프레임워크를 사용하여 LLM 체인을 구성한다.
- 시스템은 DB에 저장된 사용자의 관심종목(watchlist) 및 종목-테마(stock_theme) 데이터를 LangChain 프롬프트 컨텍스트로 주입하여 질문에 답변한다.
- 사용자의 관심종목 도메인과 무관한 질문에 대해서는 범위 밖임을 안내한다.
- `user_token` 쿠키로 인증된 사용자만 사용 가능하다.
- 투자 추천은 생성하지 않는다.

**Todo**
1. [x] LangChain(`langchain`, `langchain-openai`) 라이브러리를 설치하고 Infrastructure에 구성한다
2. [x] DB의 watchlist + stock_theme 데이터를 LangChain 프롬프트 컨텍스트로 구성하는 Domain Service를 구현한다
3. [x] `MarketDataRepositoryPort` / `LangChainQAPort` Port를 정의한다
4. [x] `AnalyzeMarketQueryUseCase`를 구현한다
5. [x] 질문/답변 Request/Response DTO를 정의한다
6. [x] `MarketDataRepositoryImpl` (watchlist + stock_theme DB 조회) 구현한다
7. [x] `LangChainQAAdapter` (ChatOpenAI + LCEL 체인) 구현한다
8. [x] `POST /market-analysis/ask` 엔드포인트를 정의하고 의존성 주입을 설정한다
9. [x] `main.py`에 라우터를 등록한다

**관련**
- [BL-BE-51](BL-BE-51-recommendation-reason-llm.md) — LLM Responses 인프라
- [BL-BE-23](BL-BE-23-stock-theme-mapping.md) — 종목-테마 매핑

**개정 이력**
- 2026-03-31: 초안 및 구현
