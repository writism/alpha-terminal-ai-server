"""ADMIN 역할 전용 FastAPI 의존성."""
from fastapi import Cookie, HTTPException
from typing import Optional

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.auth.domain.value_object.user_role import UserRole
from app.infrastructure.cache.redis_client import redis_client

_session_adapter = RedisSessionAdapter(redis_client)


def require_admin(
    session_token: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
) -> str:
    """ADMIN 역할 확인. 아니면 403 반환.

    Returns:
        인증된 account_id (str)
    """
    token = session_token or user_token
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    session = _session_adapter.find_by_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")

    if session.role not in (UserRole.ADMIN,):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

    return session.user_id
