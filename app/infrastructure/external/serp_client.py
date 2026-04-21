"""BL-BE-59: SERP API 공용 HTTP 클라이언트 — Infrastructure Layer.

- 환경 변수(settings)에서 api_key, base_url, timeout 로드
- 오류 응답 시 명확한 예외 발생 + 에러 로그
- 네트워크 오류·타임아웃에 대한 재시도(3회, 지수 백오프) 정책
- Base URL 교체는 SERP_BASE_URL 환경 변수 변경만으로 가능
"""
import logging
import time
from typing import Any, Dict

import httpx

from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 1.0  # seconds


class SerpApiError(Exception):
    """SERP API 호출 실패 예외."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class SerpClient:
    # 프로세스 전역에서 재사용되는 httpx.Client (커넥션 풀링으로 TLS/TCP 재연결 비용 제거)
    _shared_client: httpx.Client | None = None

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.serp_api_key
        self._base_url = settings.serp_base_url
        self._timeout = settings.serp_timeout

    @classmethod
    def _get_client(cls) -> httpx.Client:
        if cls._shared_client is None:
            cls._shared_client = httpx.Client(
                timeout=get_settings().serp_timeout,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return cls._shared_client

    @classmethod
    def close(cls) -> None:
        """BL-BE-85: lifespan shutdown 에서 호출 — 커넥션 풀 정리."""
        if cls._shared_client is not None:
            cls._shared_client.close()
            cls._shared_client = None

    def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """SERP API GET 요청. 재시도 포함. 인증 파라미터 자동 주입."""
        all_params = {**params, "api_key": self._api_key}
        client = self._get_client()

        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = client.get(self._base_url, params=all_params, timeout=self._timeout)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "[SerpClient] HTTP 오류 (attempt %d/%d): status=%d url=%s",
                    attempt,
                    _MAX_RETRIES,
                    e.response.status_code,
                    self._base_url,
                )
                raise SerpApiError(
                    f"SERP API 응답 오류: {e.response.status_code}",
                    status_code=e.response.status_code,
                ) from e
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(
                    "[SerpClient] 네트워크/타임아웃 오류 (attempt %d/%d): %s",
                    attempt,
                    _MAX_RETRIES,
                    e,
                )
                last_exc = e
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))

        raise SerpApiError(f"SERP API 재시도 {_MAX_RETRIES}회 실패: {last_exc}") from last_exc
