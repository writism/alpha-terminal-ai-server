# BL-BE-17

**Backlog Type**  
API / Integration

**Backlog Title**  
Twelve Data `time_series`에 `exchange` 전달 — 티커 모호성 완화

---

## 1. 배경

- 미국장은 DB·추론으로 `NASDAQ` / `NYSE`를 알 수 있는 경우가 많다.
- Twelve Data는 `exchange` 파라미터로 동일 티커 충돌 가능성을 줄일 수 있다.

## 2. 목표

| ID | 기준 |
|----|------|
| SC-1 | `market`이 `NASDAQ` 또는 `NYSE`일 때 **해당 거래소 코드**를 쿼리에 넣는다. |
| SC-2 | `exchange` 생략이 필요한 경우(미상 시장·추론 기본값)는 **기존처럼 symbol만** 호출한다. |

## 3. 매핑

- `NASDAQ` → `NASDAQ`
- `NYSE` → `NYSE`

## 4. 관련 백로그

- **BL-BE-14**

## 5. 완료 정의

- [x] `fetch_daily_closes_from_twelve_data(..., exchange=...)` 및 use case에서 `market_label` 전달.
