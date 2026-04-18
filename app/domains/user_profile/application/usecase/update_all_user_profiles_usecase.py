import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domains.user_profile.application.port.user_profile_repository_port import UserProfileRepositoryPort
from app.domains.user_profile.domain.entity.user_interaction import InteractionType
from app.domains.user_profile.domain.entity.user_profile import UserProfile

logger = logging.getLogger(__name__)

_INTERACTION_WEIGHTS = {
    InteractionType.CLICK: 1.0,
    InteractionType.LIKE: 2.0,
    InteractionType.COMMENT: 3.0,
}


class UpdateAllUserProfilesUseCase:
    """매일 자정 전체 사용자 interest_score 기반 preferred_stocks 갱신."""

    def __init__(self, repo: UserProfileRepositoryPort):
        self._repo = repo

    def execute(self) -> int:
        """전체 사용자 프로필 업데이트. 갱신된 사용자 수 반환."""
        today = datetime.now(ZoneInfo("Asia/Seoul")).date()
        account_ids = self._repo.find_all_account_ids()
        updated = 0

        for account_id in account_ids:
            interactions = self._repo.find_today_interactions(account_id, today)
            if not interactions:
                continue

            # 심볼별 interest_score 계산
            scores: dict[str, float] = {}
            for interaction in interactions:
                weight = _INTERACTION_WEIGHTS.get(interaction.interaction_type, 1.0)
                scores[interaction.symbol] = (
                    scores.get(interaction.symbol, 0.0) + interaction.count * weight
                )

            # 당일 고관심 종목 내림차순 정렬
            sorted_symbols = sorted(scores.keys(), key=lambda s: scores[s], reverse=True)

            # 기존 프로필 조회 또는 신규 생성
            profile = self._repo.find_by_account_id(account_id) or UserProfile(account_id=account_id)

            # 당일 고관심 종목 앞에 두고 기존 종목 뒤에 병합
            existing_others = [s for s in profile.preferred_stocks if s not in sorted_symbols]
            profile.preferred_stocks = sorted_symbols + existing_others

            self._repo.save(profile)
            updated += 1
            logger.debug(
                "[ProfileUpdate] account_id=%d preferred_stocks 갱신: %s",
                account_id,
                sorted_symbols,
            )

        return updated
