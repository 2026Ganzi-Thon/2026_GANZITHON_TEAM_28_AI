from typing import Any


def api_response(
    *,
    is_success: bool = True,
    code: str = "COMMON200",
    message: str = "요청에 성공했습니다.",
    result: Any = None,
) -> dict:
    """팀 공통 ApiResponse 형식 (isSuccess, code, message, result)."""
    return {
        "isSuccess": is_success,
        "code": code,
        "message": message,
        "result": result,
    }
