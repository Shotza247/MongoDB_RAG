from fastapi import FastAPI
from fastapi.testclient import TestClient

from mongodb_vector_test_ui.api.fastapi import app

EXPECTED_ROUTES = {
    ("/", "GET"),
    ("/api/health", "GET"),
    ("/api/status", "GET"),
    ("/api/mongodb/databases", "GET"),
    ("/api/mongodb/collections", "GET"),
    ("/api/mongodb/collection/summary", "GET"),
    ("/api/index/create", "POST"),
    ("/api/document/extract/upload", "POST"),
    ("/api/document/extract/path", "POST"),
    ("/api/document/chunks", "POST"),
    ("/api/index/document", "POST"),
    ("/api/search", "POST"),
    ("/api/rerank", "POST"),
    ("/api/ask", "POST"),
}


def test_fastapi_is_primary_application() -> None:
    assert isinstance(app, FastAPI)
    assert app.title == "MongoDB RAG API"


def test_fastapi_preserves_mvp1_route_contract() -> None:
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
        if method in {"GET", "POST"}
    }

    assert EXPECTED_ROUTES <= routes


def test_fastapi_exposes_openapi_for_api_routes() -> None:
    schema = app.openapi()

    assert "/api/health" in schema["paths"]
    assert "/api/status" in schema["paths"]
    assert "/api/index/document" in schema["paths"]
    assert "/api/search" in schema["paths"]
    assert "/api/rerank" in schema["paths"]
    assert "/api/ask" in schema["paths"]


def test_health_endpoint_returns_liveness_without_database_access() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_fastapi_allows_local_portfolio_origin_for_ask() -> None:
    response = TestClient(app).options(
        "/api/ask",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_fastapi_allows_local_portfolio_origin_for_health() -> None:
    response = TestClient(app).options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_fastapi_rejects_unconfigured_portfolio_origin() -> None:
    response = TestClient(app).options(
        "/api/ask",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_browser_ui_chains_search_and_reranking() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Embed Query, Search, and Rerank" in response.text
    assert 'callJson("/api/search"' in response.text
    assert 'callJson("/api/rerank"' in response.text
    assert "vector_score" in response.text
    assert "rerank_score" in response.text
