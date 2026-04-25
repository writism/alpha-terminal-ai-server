import logging
from typing import Optional

from app.domains.auth.application.response.me_response import MeResponse
from app.domains.auth.application.usecase.session_store_port import SessionStorePort
from app.domains.auth.application.usecase.temp_token_check_port import TempTokenCheckPort

logger = logging.getLogger(__name__)


class GetMeUseCase:

    def __init__(self, session_store: SessionStorePort, temp_token_check: TempTokenCheckPort):
        self._session_store = session_store
        self._temp_token_check = temp_token_check

    def execute(
        self,
        user_token: Optional[str],
        temp_token: Optional[str],
        nickname: Optional[str],
        email: Optional[str],
        kakao_nickname: Optional[str],
        kakao_email: Optional[str],
    ) -> MeResponse:
        if user_token:
            session = self._session_store.find_by_token(user_token)
            if session:
                logger.debug("[GetMe] session found account_id=%s token_prefix=%s...", session.user_id, user_token[:8])
                return MeResponse(
                    is_registered=True,
                    email=email or "",
                    nickname=nickname,
                    account_id=session.user_id,
                )

        if temp_token and self._temp_token_check.exists(temp_token):
            logger.debug("[GetMe] temp_token found prefix=%s...", temp_token[:8])
            return MeResponse(
                is_registered=False,
                email=kakao_email or "",
                nickname=kakao_nickname,
            )

        raise PermissionError("유효한 토큰이 없습니다.")
