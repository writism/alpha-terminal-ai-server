"""BL-BE-55: user_profile Mock Repository.

1단계(최승호/이하연) DB 구현 전까지 임시 mock 데이터를 반환한다.
실제 DB 구현 완료 후 이 파일을 DB 기반 구현체로 교체한다.
"""
from app.domains.user_profile.domain.entity.user_profile import UserProfile

_MOCK_PROFILES = {
    1: UserProfile(
        account_id=1,
        investment_style="중장기",
        risk_tolerance="중간",
        preferred_sectors=["IT", "반도체", "플랫폼"],
        analysis_preference="뉴스중심",
        watchlist_symbols=["060250", "005930", "035420"],
        keywords_of_interest=["AI반도체", "클라우드", "B2B SaaS"],
    ),
    2: UserProfile(
        account_id=2,
        investment_style="단기",
        risk_tolerance="높음",
        preferred_sectors=["바이오", "2차전지"],
        analysis_preference="공시중심",
        watchlist_symbols=["234340", "373220"],
        keywords_of_interest=["임상3상", "전고체배터리"],
    ),
    3: UserProfile(
        account_id=3,
        investment_style="장기",
        risk_tolerance="낮음",
        preferred_sectors=["금융", "통신", "유틸리티"],
        analysis_preference="혼합",
        watchlist_symbols=["105560", "017670"],
        keywords_of_interest=["배당", "안정성", "실적"],
    ),
}


class MockUserProfileRepository:
    def get_by_account_id(self, account_id: int) -> UserProfile | None:
        return _MOCK_PROFILES.get(account_id)
