# BL-BE-14

**Backlog Type**  
API / Integration / Cost-control Backlog

**Backlog Title**  
히트맵 시계열 공급자를 권장안 A로 전환한다 (`data.go.kr` KRX + Twelve Data US)

---

## 1. 배경 / 문제

- **BL-BE-13**에서 히트맵 API 자체(`GET /stocks/daily-returns-heatmap`)는 만들었지만, 초기 공급자였던 **Finnhub `stock/candle`** 이 현재 키/플랜에서 **403 Forbidden** 을 반환하고 있다.
- 결과적으로 프론트는 요청은 정상적으로 보내지만 `items: []`, `errors: [NO_DATA...]` 만 받게 되어 히트맵이 렌더되지 않는다.
- 검색(`Finnhub /search`)은 무료로 동작하므로, **검색 공급자와 히스토리 공급자를 분리**해도 UX는 성립한다.

---

## 2. 목표 (Success Criteria)

| ID | 기준 |
|----|------|
| SC-1 | 히트맵 API는 **한국장(KOSPI/KOSDAQ/KONEX)** 심볼을 **`data.go.kr` 금융위원회_주식시세정보**에서 조회한다. |
| SC-2 | 히트맵 API는 **미국장(NASDAQ/NYSE)** 심볼을 **Twelve Data `time_series`** 에서 조회한다. |
| SC-3 | 기존 `GET /stocks/daily-returns-heatmap` 응답 계약(`as_of`, `weeks`, `items[]`, `errors[]`)은 유지한다. |
| SC-4 | 동일 심볼·동일 기간 요청은 **서버 메모리 캐시**로 흡수해 외부 호출 수를 줄인다. |
| SC-5 | 공급자 키가 없거나 공급자 요청이 막힌 경우, 해당 심볼만 `errors[]`에 원인을 담고 **부분 성공**을 허용한다. |
| SC-6 | 로그에 **토큰/서비스키가 노출되지 않는다**. |

---

## 3. 권장 솔루션 (권장안 A)

### 3.1 공급자 라우팅

| market | 공급자 | 비고 |
|--------|--------|------|
| `KOSPI`, `KOSDAQ`, `KONEX` | `data.go.kr` `getStockPriceInfo` | 무료, 일 1회 갱신, T+1 성격 |
| `NASDAQ`, `NYSE` | Twelve Data `time_series` | 무료 Basic 기준 US 지원 |
| 기타 / 미상 | 심볼 형식·DB market에 따라 최대한 추론, 불가 시 `UNSUPPORTED_MARKET` |

### 3.2 비용 최소화

1. **기간 상한 고정**
   - `weeks`는 1~13으로 제한
   - 실제 외부 조회는 대략 최근 70일 캘린더 구간만
2. **메모리 캐시**
   - 키: `(provider, symbol, weeks, date-bucket)`
   - 한국장은 장중 실시간이 아니므로 비교적 긴 TTL 가능
3. **배치 API는 유지**
   - 프론트는 심볼 목록을 한 번에 보내고, 서버가 시장별 공급자를 나눠 호출

---

## 4. API / 데이터 계약

### 4.1 입력

- `GET /stocks/daily-returns-heatmap?symbols=005930,AAPL&weeks=6`

### 4.2 출력

기존 BL-BE-13 계약 유지:

```json
{
  "as_of": "2026-03-24",
  "weeks": 6,
  "items": [
    {
      "symbol": "AAPL",
      "market": "NASDAQ",
      "series": [["2026-02-12", 1], ["2026-02-13", -1]],
      "summary": { "up": 12, "down": 8, "flat": 2 }
    }
  ],
  "errors": [
    { "symbol": "005930", "code": "NO_PROVIDER_KEY", "message": "..." }
  ]
}
```

---

## 5. 구현 작업 분해

1. [ ] 환경변수 추가  
   - `DATA_GO_KR_SERVICE_KEY`  
   - `TWELVE_DATA_API_KEY`
2. [x] `data.go.kr` 어댑터 구현  
   - `getStockPriceInfo` 호출  
   - `beginBasDt`, `endBasDt`, `likeSrtnCd`, `resultType=json` 사용  
   - `clpr`, `basDt`, `srtnCd` 파싱  
   - **`pageNo` 순회로 페이징**(한 페이지 `numOfRows`를 넘는 구간도 수집, 동일 일자 중복은 마지막 값으로 병합) — BL-BE-13 §9
3. [ ] Twelve Data 어댑터 구현  
   - `/time_series?symbol=AAPL&interval=1day&outputsize=N`
   - `values[].datetime`, `close` 파싱
4. [ ] 일봉 close 시퀀스 → bucket 시퀀스 변환
5. [ ] 시장별 provider routing + 캐시 + 부분 실패
6. [ ] Finnhub candle 의존 제거

---

## 6. 리스크 / 제약

- `data.go.kr`는 **실시간이 아니라 전일/지연 데이터**다. 히트맵 용도에는 허용 가능하다.
- Twelve Data 무료 플랜은 **KRX 전체 시장이 아니라 US 중심**이므로, 한국장은 이 공급자로 해결하지 않는다.
- 미국 티커가 watchlist에 저장될 때 `market`이 비어 있어도 **비숫자 티커는 US**로 추정 가능하지만, 정확도는 watchlist 저장 시 `market` 전달에 의존한다.

---

## 7. 관련 백로그

- **BL-BE-13**: 히트맵 API 일반 설계
- **BL-BE-15**: Redis 공유 캐시
- **BL-BE-16**: `get_settings` 핫리로드
- **BL-BE-17**: Twelve Data `exchange`
- **BL-FE-31**: 권장안 A 기준 프론트 캐시·UX 조정

---

## 8. 완료 정의 (Definition of Done)

- [ ] 한국장 심볼 1개 이상, 미국장 심볼 1개 이상에 대해 동일 API에서 `items[]`가 채워진다.
- [ ] Finnhub `stock/candle` 경로가 히트맵 실행에 더 이상 필요하지 않다.
- [ ] 키/서비스 장애 시 `errors[]`에 심볼별 원인이 남고, 다른 심볼은 계속 표시된다.
