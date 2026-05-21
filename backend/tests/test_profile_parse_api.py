from fastapi.testclient import TestClient


def test_profile_parse_returns_mock_user_profile(client: TestClient) -> None:
    response = client.post(
        "/api/v1/profile/parse",
        json={
            "profile_text": (
                "Product analyst with SQL, Python, dashboarding, A/B testing, "
                "and stakeholder communication experience."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_profile"]["name"] == "Alex Chen"
    assert len(body["user_profile"]["experiences"]) >= 1
    assert "Python" in body["user_profile"]["skills"]


def test_profile_parse_accepts_short_sparse_profile_text(client: TestClient) -> None:
    response = client.post(
        "/api/v1/profile/parse",
        json={"profile_text": "仅有教育背景和基础技能"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_profile"]["name"] == "Alex Chen"
