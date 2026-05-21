from fastapi.testclient import TestClient


def test_jd_analyze_returns_mock_profile(client: TestClient) -> None:
    response = client.post(
        "/api/v1/jd/analyze",
        json={
            "raw_jd": (
                "Senior Product Data Analyst\n"
                "Own product metrics, SQL analysis, dashboarding, and experiment readouts."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["jd_profile"]["position"]
    assert "SQL" in body["jd_profile"]["required_skills"]
    assert body["jd_profile"]["resume_strategy"]["must_highlight"]
