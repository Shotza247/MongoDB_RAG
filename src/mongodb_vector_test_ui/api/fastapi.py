from __future__ import annotations

from collections.abc import Callable, Sequence

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from mongodb_vector_test_ui.api import starlette as starlette_reference
from mongodb_vector_test_ui.core.config import get_settings

Handler = Callable[[Request], Response]


def create_app() -> FastAPI:
    app = FastAPI(
        title="MongoDB RAG API",
        summary="Reusable MongoDB retrieval and reranking service",
        description=(
            "MVP2 FastAPI entry point. It preserves the verified MVP1 HTTP contract "
            "for the browser and Streamlit evaluation clients."
        ),
        version="0.2.0",
        debug=get_settings().app_env == "local",
    )

    routes: Sequence[tuple[str, Handler, list[str], str, str]] = (
        ("/", starlette_reference.home, ["GET"], "Test UI", "ui"),
        ("/api/status", starlette_reference.status, ["GET"], "Service status", "system"),
        (
            "/api/mongodb/databases",
            starlette_reference.mongodb_databases,
            ["GET"],
            "List MongoDB databases",
            "mongodb",
        ),
        (
            "/api/mongodb/collections",
            starlette_reference.mongodb_collections,
            ["GET"],
            "List MongoDB collections",
            "mongodb",
        ),
        (
            "/api/mongodb/collection/summary",
            starlette_reference.mongodb_collection_summary,
            ["GET"],
            "Inspect a MongoDB collection",
            "mongodb",
        ),
        (
            "/api/index/create",
            starlette_reference.create_index,
            ["POST"],
            "Create or inspect the vector index",
            "indexing",
        ),
        (
            "/api/document/extract/upload",
            starlette_reference.extract_uploaded_document,
            ["POST"],
            "Extract an uploaded document",
            "documents",
        ),
        (
            "/api/document/extract/path",
            starlette_reference.extract_path_document,
            ["POST"],
            "Extract a local document path",
            "documents",
        ),
        (
            "/api/document/chunks",
            starlette_reference.preview_chunks,
            ["POST"],
            "Preview document chunks",
            "documents",
        ),
        (
            "/api/index/document",
            starlette_reference.index_document,
            ["POST"],
            "Chunk, embed, and store a document",
            "indexing",
        ),
        (
            "/api/search",
            starlette_reference.search,
            ["POST"],
            "Run MongoDB vector search",
            "retrieval",
        ),
        (
            "/api/rerank",
            starlette_reference.rerank,
            ["POST"],
            "Rerank retrieved candidates",
            "retrieval",
        ),
        (
            "/api/ask",
            starlette_reference.ask,
            ["POST"],
            "Retrieve evidence and generate a cited answer",
            "answering",
        ),
    )

    for path, endpoint, methods, summary, tag in routes:
        app.add_api_route(
            path,
            endpoint,
            methods=methods,
            summary=summary,
            tags=[tag],
            include_in_schema=path != "/",
        )

    return app


app = create_app()
