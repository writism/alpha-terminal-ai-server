from app.domains.user_profile.application.port.user_profile_repository_port import UserProfileRepositoryPort
from app.domains.user_profile.application.request.save_clicked_card_request import SaveClickedCardRequest
from app.domains.user_profile.application.response.user_profile_response import SaveClickedCardResponse
from app.domains.user_profile.domain.entity.user_interaction import UserInteraction, InteractionType


class SaveClickedCardUseCase:
    MAX_CLICKED_CARDS = 10

    def __init__(self, repository: UserProfileRepositoryPort):
        self._repository = repository

    def execute(self, account_id: int, request: SaveClickedCardRequest) -> SaveClickedCardResponse:
        interaction = UserInteraction(
            account_id=account_id,
            symbol=request.symbol,
            name=request.name,
            market=request.market,
            interaction_type=InteractionType.CLICK,
            count=1,
        )
        saved = self._repository.upsert_clicked_card(interaction)
        self._repository.enforce_max_recently_viewed(account_id, self.MAX_CLICKED_CARDS)

        return SaveClickedCardResponse(
            symbol=saved.symbol,
            name=saved.name or "",
            market=saved.market,
            count=saved.count,
        )
