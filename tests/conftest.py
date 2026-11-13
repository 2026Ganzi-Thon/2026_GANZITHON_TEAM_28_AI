import os

# app을 import하기 전에 테스트용 환경값을 고정한다.
os.environ["AI_INTERNAL_KEY"] = "test-key"
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def headers():
    return {"X-Internal-Key": "test-key", "X-Request-Id": "test-req-1"}
