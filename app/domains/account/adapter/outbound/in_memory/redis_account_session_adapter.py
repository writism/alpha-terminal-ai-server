import uuid

import redis

from app.domains.account.application.usecase.account_session_store_port import AccountSessionStorePort
from app.domains.auth.domain.entity.session import Session
from app.domains.auth.domain.value_object.user_role import UserRole
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter

SESSION_TTL_SECONDS = 3600 * 24 * 7  # 7일
KAKAO_TOKEN_KEY_PREFIX = "kakao_token:"
KAKAO_TOKEN_TTL_SECONDS = 3600 * 24 * 7  # 7일


class RedisAccountSessionAdapter(AccountSessionStorePort):

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._session_adapter = RedisSessionAdapter(redis_client)

    def create_session(self, account_id: int) -> str:
        return self.create(account_id)

    def create(self, account_id: int) -> str:
        token = str(uuid.uuid4())
        session = Session(token=token, user_id=str(account_id), role=UserRole.USER, ttl_seconds=SESSION_TTL_SECONDS)
        self._session_adapter.save(session)
        return token

    def save_account_kakao_token(self, account_id: int, kakao_access_token: str) -> None:
        key = KAKAO_TOKEN_KEY_PREFIX + str(account_id)
        self._redis.setex(key, KAKAO_TOKEN_TTL_SECONDS, kakao_access_token)

    def delete(self, session_token: str) -> None:
        self._session_adapter.delete(session_token)
