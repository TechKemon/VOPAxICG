import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from myca_recsys.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_courses_endpoint_returns_catalog():
    response = client.get("/v1/courses")

    assert response.status_code == 200
    assert len(response.json()) >= 8


def test_recommendations_endpoint_returns_ranked_courses():
    response = client.post(
        "/v1/recommendations",
        json={
            "profile": {
                "feelings": ["anxious"],
                "challenges": ["exam pressure", "fear of failure"],
                "goals": ["manage stress"],
                "risk_signals": [],
            },
            "top_n": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["recommendations"]) == 3
    assert payload["recommendations"][0]["id"] == "C008"
    assert payload["safety"]["is_crisis"] is False
