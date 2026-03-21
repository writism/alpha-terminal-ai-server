from app.domains.account.application.usecase.account_session_port import AccountSessionPort


class LogoutAccountUseCase:
    def __init__(self, session_port: AccountSessionPort):
        self._session_port = session_port

    def execute(self, session_token: str) -> None:
        self._session_port.delete(session_token)
