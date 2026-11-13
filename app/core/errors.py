import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import api_response

logger = logging.getLogger("ai")


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code


def unauthorized() -> AppError:
    return AppError("AI401", "내부 인증에 실패했습니다.", 401)


def bad_response() -> AppError:
    return AppError("AI502", "AI 응답 형식이 올바르지 않습니다.", 502)


def unavailable() -> AppError:
    return AppError("AI503", "AI 호출에 실패했습니다.", 503)


def timeout() -> AppError:
    return AppError("AI504", "AI 응답 시간이 초과되었습니다.", 504)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _error_json(request: Request, status: int, code: str, message: str) -> JSONResponse:
    body = api_response(
        is_success=False,
        code=code,
        message=f"{message} (requestId={_request_id(request)})",
    )
    return JSONResponse(status_code=status, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return _error_json(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        # 입력 원문은 에러 메시지에 넣지 않고 문제가 된 필드 경로만 알려준다.
        fields = sorted({".".join(str(p) for p in e["loc"] if p != "body") for e in exc.errors()})
        return _error_json(
            request, 400, "COMMON400_1", f"입력값 검증에 실패했습니다: {', '.join(fields)}"
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.error("unexpected error requestId=%s type=%s", _request_id(request), type(exc).__name__)
        return _error_json(request, 500, "COMMON500", "서버 내부 오류가 발생했습니다.")
