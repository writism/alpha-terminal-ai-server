from abc import ABC, abstractmethod


class AccountSessionPort(ABC):

    @abstractmethod
    def create(self, account_id: int) -> str:
        """account_id를 user_id로 하는 세션을 생성하고 session_token을 반환한다."""
        pass

    @abstractmethod
    def link_kakao_token(self, kakao_access_token: str, account_id: int) -> None:
        """Kakao 액세스 토큰을 account_id와 연결하여 Redis에 저장한다."""
        pass

    @abstractmethod
    def save_account_kakao_token(self, account_id: int, kakao_access_token: str) -> None:
        """account_id를 key로 kakao_access_token을 Redis에 저장한다."""
        pass

    @abstractmethod
    def delete(self, session_token: str) -> None:
        """session_token에 해당하는 세션을 Redis에서 삭제한다."""
        pass
