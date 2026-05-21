from fastapi.testclient import TestClient


def test_jd_api_rejects_blank_raw_jd(client: TestClient) -> None:
    response = client.post("/api/v1/jd/analyze", json={"raw_jd": "   "})

    assert response.status_code in {400, 422}


def test_jd_api_rejects_missing_raw_jd(client: TestClient) -> None:
    response = client.post("/api/v1/jd/analyze", json={})

    assert response.status_code in {400, 422}
