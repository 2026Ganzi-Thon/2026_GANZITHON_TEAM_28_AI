import logging
import time
import uuid

from fastapi import FastAPI, Request

logger = logging.getLogger("ai")


def register_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        # 요청 본문(사용자 입력)은 절대 로그에 남기지 않는다.
        logger.info(
            "requestId=%s %s %s status=%s ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-Id"] = request_id
        return response
