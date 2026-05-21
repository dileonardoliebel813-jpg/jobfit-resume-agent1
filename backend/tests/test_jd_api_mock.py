from fastapi.testclient import TestClient


def test_jd_api_returns_mock_profile(client: TestClient) -> None:
    response = client.post(
        "/api/v1/jd/analyze",
        json={"raw_jd": "高级产品数据分析师\n负责 SQL 分析、Python 数据处理和产品实验复盘。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "jd_profile" in body
    assert body["jd_profile"]["position"]
    assert body["jd_profile"]["resume_strategy"]["tone"]
