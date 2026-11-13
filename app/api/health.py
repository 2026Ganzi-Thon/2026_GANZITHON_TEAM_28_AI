from fastapi import APIRouter

from app.core.response import api_response

router = APIRouter(tags=["health"])


@router.get("/health", summary="헬스체크 (내부 키 불필요)")
async def health():
    return api_response(result={"status": "UP"})
