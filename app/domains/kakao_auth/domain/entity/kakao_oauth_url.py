from dataclasses import dataclass
from typing import Optional
from app.domains.kakao_auth.domain.value_object.kakao_oauth_params import KakaoOAuthParams

KAKAO_AUTH_BASE_URL = "https://kauth.kakao.com/oauth/authorize"


@dataclass
class KakaoOAuthUrl:
    params: KakaoOAuthParams

    def build(self, state: Optional[str] = None) -> str:
        url = (
            f"{KAKAO_AUTH_BASE_URL}"
            f"?client_id={self.params.client_id}"
            f"&redirect_uri={self.params.redirect_uri}"
            f"&response_type={self.params.response_type}"
            f"&scope=profile_nickname"
            f"&prompt=login"
        )
        if state:
            url += f"&state={state}"
        return url
