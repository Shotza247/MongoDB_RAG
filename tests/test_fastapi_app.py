from fastapi import FastAPI
from fastapi.testclient import TestClient

from mongodb_vector_test_ui.api.fastapi import app

EXPECTED_ROUTES = {
    ("/", "GET"),
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

    assert "/api/status" in schema["paths"]
    assert "/api/index/document" in schema["paths"]
    assert "/api/search" in schema["paths"]
    assert "/api/rerank" in schema["paths"]
    assert "/api/ask" in schema["paths"]


def test_browser_ui_chains_search_and_reranking() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Embed Query, Search, and Rerank" in response.text
    assert 'callJson("/api/search"' in response.text
    assert 'callJson("/api/rerank"' in response.text
    assert "vector_score" in response.text
    assert "rerank_score" in response.text
