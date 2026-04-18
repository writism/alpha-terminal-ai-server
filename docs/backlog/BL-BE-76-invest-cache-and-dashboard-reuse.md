# BL-BE-76

**Backlog Type**
Bug Fix + UseCase Backlog

**Backlog Title**
INVEST 종목 분석 시 스트림 엔드포인트에 캐시를 적용하고 대시보드 분석 결과를 Retrieval 컨텍스트로 재활용한다

---

## 배경 및 문제

INVEST 페이지에서 종목을 분석할 때 아래 두 가지 문제가 있었다.

### 문제 1: 스트림 엔드포인트에 캐시 없음

`/investment/decision/stream`(프론트엔드가 실제 사용하는 엔드포인트)에는 캐시 로직이 전혀 없었다.
`/investment/decision`(non-stream)에만 `AnalysisCacheRepository` 기반 1시간 TTL 캐시가 존재했으나
프론트엔드는 이 엔드포인트를 사용하지 않았기 때문에 사실상 캐시가 동작하지 않았다.

결과: 같은 종목을 반복 조회해도 매번 Orchestrator → Retrieval → Analysis → Synthesis 전체 파이프라인이 재실행되었다.

### 문제 2: 대시보드 분석 결과와 INVEST 에이전트 완전 단절

대시보드 파이프라인이 `analysis_logs` 테이블에 종목별 AI 분석 요약을 저장해두어도,
INVEST의 Retrieval 노드는 이 데이터를 전혀 참조하지 않고 뉴스·YouTube·DART를 처음부터 재수집했다.

결과: 대시보드에서 분석된 종목도 INVEST에서는 동일 컨텍스트를 활용하지 못하고 중복 수집이 발생했다.

### 추가 문제: `symbol` 필드 미전송으로 stream 요청 422 가능성

`InvestmentDecisionRequest.symbol`이 required(`...`)로 선언되어 있었으나
프론트엔드 `streamInvestmentDecision`은 `{ query }`만 전송했다.

---

## 해결 방안

### Fix 1: `symbol` Optional 처리

`InvestmentDecisionRequest.symbol`을 `Optional[str] = None`으로 변경.
- `/decision` (non-stream): symbol 미전송 시 422 반환 (명시적 검증으로 대체)
- `/decision/stream`: symbol 없이도 동작 가능, 내부에서 자동 조회

### Fix 2: 스트림 엔드포인트 캐시 로직 추가

**symbol 확정 흐름:**
1. `request.symbol`이 있으면 그대로 사용
2. 없으면 QueryParser로 `company`명 추출 → `stocks` DB에서 `symbol` 조회

**캐시 흐름:**
1. symbol 확정 후 `analysis_cache` 테이블에서 유효 캐시(1시간 이내) 조회
2. 캐시 히트: `[Cache] ✓` 로그 이벤트 + 캐시된 결과를 SSE 스트림으로 즉시 반환
3. 캐시 미스: 전체 워크플로우 실행 → 완료 후 결과를 symbol 기준으로 캐시 저장

### Fix 3: Retrieval에 `"대시보드 분석"` 소스 추가

`analysis_logs` 테이블에서 최근 48시간 내 해당 종목의 분석 기록을 조회하여
Retrieval 결과에 포함시킨다.

**조회 조건:** `symbol` (company명 → stocks DB로 symbol 매핑) + `analyzed_at >= now - 48h`
**정렬:** `analyzed_at DESC LIMIT 5`
**포함 내용:** 분석 일시, 소스 타입, 감성/점수/신뢰도, 태그, 요약

---

## 변경 파일

### BE

| 파일 | 변경 내용 |
|------|-----------|
| `application/request/investment_decision_request.py` | `symbol: Optional[str] = None`으로 변경 |
| `adapter/inbound/api/investment_router.py` | stream 엔드포인트에 symbol 자동 조회 + 캐시 hit/miss/save 로직 추가; `_lookup_symbol_by_name`, `_find_cached_answer`, `_save_cache` 헬퍼 추가 |
| `adapter/outbound/agent/retrieval_node.py` | `_handle_dashboard_analysis` 핸들러 추가; `SOURCE_REGISTRY`에 `"대시보드 분석"` 등록 |
| `adapter/outbound/agent/query_parser.py` | `SOURCE_REGISTRY`에 `"대시보드 분석"` 등록; `DEFAULT_SOURCES` 추가; 시스템 프롬프트 업데이트 (선택 기준 + 예시) |

### FE

변경 없음. symbol을 BE에서 자동 조회하므로 프론트엔드 수정 불필요.

---

## 동작 흐름 (수정 후)

```
사용자: "삼성전자 지금 매수해도 될까요?"
  ↓
[stream endpoint]
  QueryParser → company = "삼성전자"
  stocks DB → symbol = "005930"
  analysis_cache 조회 → hit: 즉시 반환 (워크플로우 없음)
                      → miss: 워크플로우 실행
                            Retrieval: 뉴스 + YouTube + 종목 + 대시보드 분석 (analysis_logs)
                            Analysis → Synthesis
                            완료 후 analysis_cache 저장 (TTL 1h)
```

---

## 캐시 TTL

| 항목 | 값 |
|------|----|
| `analysis_cache` TTL | 1시간 (`CACHE_TTL_HOURS = 1`) |
| 대시보드 분석 조회 범위 | 최근 48시간 |

---

## 제약 사항

- `"대시보드 분석"` 소스는 종목(company)이 추출된 경우에만 유효한 결과를 반환한다.
  섹터 질문("방산주 전반 전망") 등 company=None 케이스는 빈 결과(`""`)를 반환하며 Retrieval에서 자동 제외된다.
- QueryParser 선행 실행(~1s)이 캐시 조회 전에 발생하므로 캐시 히트 시도 약 1초의 초기 지연이 존재한다.
  symbol을 프론트에서 직접 전송하면 이 지연을 제거할 수 있다.
