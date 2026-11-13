import hmac

from fastapi import Header

from app.core.config import get_settings
from app.core.errors import unauthorized


async def verify_internal_key(x_internal_key: str | None = Header(default=None)) -> None:
    expected = get_settings().ai_internal_key
    # 서버에 키가 설정되지 않았으면 모든 요청을 거부한다 (fail closed).
    if not expected or not x_internal_key:
        raise unauthorized()
    if not hmac.compare_digest(x_internal_key.encode(), expected.encode()):
        raise unauthorized()
