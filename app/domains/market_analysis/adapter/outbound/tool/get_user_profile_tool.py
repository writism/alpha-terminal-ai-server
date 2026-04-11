"""BL-BE-55: get_user_profile LangChain Tool.

사용자 투자 성향 프로필을 조회하여 LangChain Agent 컨텍스트로 제공한다.
현재는 MockUserProfileRepository를 사용하며,
1단계 DB 구현 완료 후 UserProfileRepositoryImpl로 교체한다.
"""
from langchain_core.tools import tool

from app.domains.user_profile.adapter.outbound.persistence.mock_user_profile_repository import (
    MockUserProfileRepository,
)

_repo = MockUserProfileRepository()


@tool
def get_user_profile(account_id: int) -> str:
    """사용자 투자 성향 프로필을 조회한다. AI가 맞춤 분석을 위해 사용자 성향을 파악할 때 호출한다."""
    profile = _repo.get_by_account_id(account_id)
    if not profile:
        return "프로필 정보 없음 — 기본 분석을 수행합니다."
    return (
        f"투자스타일:{profile.investment_style} | "
        f"위험허용도:{profile.risk_tolerance} | "
        f"관심섹터:{', '.join(profile.preferred_sectors)} | "
        f"분석선호:{profile.analysis_preference} | "
        f"관심키워드:{', '.join(profile.keywords_of_interest)}"
    )
