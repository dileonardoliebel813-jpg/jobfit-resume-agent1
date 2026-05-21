import os

import pytest
from fastapi.testclient import TestClient

os.environ["LLM_MODE"] = "mock"

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
