import logging

from fastapi import APIRouter, FastAPI

from app.api import health, steps
from app.core.errors import register_exception_handlers
from app.core.middleware import register_request_id_middleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Team28 AI Server", version="0.1.0")

register_request_id_middleware(app)
register_exception_handlers(app)

v1 = APIRouter(prefix="/ai/v1")
v1.include_router(health.router)
v1.include_router(steps.router)
app.include_router(v1)
