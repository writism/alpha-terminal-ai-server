from app.domains.kakao_auth.application.usecase.generate_kakao_oauth_url_port import GenerateKakaoOAuthUrlPort
from app.domains.kakao_auth.domain.entity.kakao_oauth_url import KakaoOAuthUrl
from app.domains.kakao_auth.domain.value_object.kakao_oauth_params import KakaoOAuthParams


class KakaoOAuthAdapter(GenerateKakaoOAuthUrlPort):

    def __init__(self, client_id: str, redirect_uri: str):
        if not client_id:
            raise ValueError("kakao_client_id is required")
        if not redirect_uri:
            raise ValueError("kakao_redirect_uri is required")
        self._client_id = client_id
        self._redirect_uri = redirect_uri

    def generate(self, state: str | None = None) -> str:
        params = KakaoOAuthParams(
            client_id=self._client_id,
            redirect_uri=self._redirect_uri,
        )
        return KakaoOAuthUrl(params=params).build(state=state)
