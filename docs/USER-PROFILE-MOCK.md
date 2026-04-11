# user_profile Mock 데이터 명세

## 개요

`user_profile`은 AI 맞춤 분석에 사용되는 사용자 투자 성향 프로필이다.
1단계(최승호/이하연) DB 구현 완료 전까지 Mock Repository를 사용한다.

> **투자 추천 용도 아님** — AI 분석 관점 개인화에만 활용

---

## 데이터 구조

```python
@dataclass
class UserProfile:
    account_id: int               # 사용자 ID
    investment_style: str         # 투자 스타일: "단기" | "중장기" | "장기"
    risk_tolerance: str           # 위험 허용도: "낮음" | "중간" | "높음"
    preferred_sectors: List[str]  # 관심 섹터: ["IT", "바이오", "금융" ...]
    analysis_preference: str      # 분석 선호: "뉴스중심" | "공시중심" | "혼합"
    watchlist_symbols: List[str]  # 관심종목 코드: ["060250", "005930" ...]
    keywords_of_interest: List[str] # 관심 키워드: ["AI반도체", "배당" ...]
```

---

## Mock 데이터 3건

### account_id=1 — IT/반도체 중장기 투자자
| 필드 | 값 |
|------|-----|
| investment_style | 중장기 |
| risk_tolerance | 중간 |
| preferred_sectors | IT, 반도체, 플랫폼 |
| analysis_preference | 뉴스중심 |
| watchlist_symbols | 060250(NHN KCP), 005930(삼성전자), 035420(NAVER) |
| keywords_of_interest | AI반도체, 클라우드, B2B SaaS |

### account_id=2 — 바이오/2차전지 단기 투자자
| 필드 | 값 |
|------|-----|
| investment_style | 단기 |
| risk_tolerance | 높음 |
| preferred_sectors | 바이오, 2차전지 |
| analysis_preference | 공시중심 |
| watchlist_symbols | 234340(헥토파이낸셜), 373220(LG에너지솔루션) |
| keywords_of_interest | 임상3상, 전고체배터리 |

### account_id=3 — 금융/통신 장기 배당 투자자
| 필드 | 값 |
|------|-----|
| investment_style | 장기 |
| risk_tolerance | 낮음 |
| preferred_sectors | 금융, 통신, 유틸리티 |
| analysis_preference | 혼합 |
| watchlist_symbols | 105560(KB금융), 017670(SK텔레콤) |
| keywords_of_interest | 배당, 안정성, 실적 |

---

## 파일 위치

```
app/domains/user_profile/
 ├ domain/entity/user_profile.py                          — Entity
 └ adapter/outbound/persistence/
     └ mock_user_profile_repository.py                   — Mock Repository
```

---

## 사용 방법 (BL-BE-55 LangChain Tool에서)

```python
from app.domains.user_profile.adapter.outbound.persistence.mock_user_profile_repository import MockUserProfileRepository

repo = MockUserProfileRepository()
profile = repo.get_by_account_id(account_id)  # UserProfile | None
```

---

## 교체 시점

1단계 완료 후 `MockUserProfileRepository` →  `UserProfileRepositoryImpl` (DB 기반)으로 교체.
LangChain Tool 코드는 수정 없이 Repository만 교체하면 된다.
