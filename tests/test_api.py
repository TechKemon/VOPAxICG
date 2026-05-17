import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from myca_recsys.api import app


client = TestClient(app)


def test_root_redirects_to_interactive_docs():
    response = client.get("/", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/docs"


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


def test_openapi_docs_include_api_key_security_scheme():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    scheme = payload["components"]["securitySchemes"]["APIKeyHeader"]
    assert scheme["type"] == "apiKey"
    assert scheme["name"] == "X-API-Key"
    assert scheme["in"] == "header"


def test_courses_endpoint_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setenv("MYCA_API_KEY", "secret-test-key")

    response = client.get("/v1/courses")

    assert response.status_code == 401


def test_courses_endpoint_accepts_valid_api_key(monkeypatch):
    monkeypatch.setenv("MYCA_API_KEY", "secret-test-key")

    response = client.get("/v1/courses", headers={"X-API-Key": "secret-test-key"})

    assert response.status_code == 200
    assert len(response.json()) >= 8
