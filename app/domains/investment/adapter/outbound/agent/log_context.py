"""투자 워크플로우 로그 컨텍스트.

DEPRECATED: `app.infrastructure.log_context` 로 통합되었다. 신규 코드는 그쪽을 사용하라.
본 모듈은 기존 호출처와의 하위 호환을 위해 동일 심볼을 re-export 한다.
"""
from app.infrastructure.log_context import (  # noqa: F401
    aemit,
    reset_log_queue,
    set_log_queue,
)
