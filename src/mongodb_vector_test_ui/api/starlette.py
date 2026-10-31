from __future__ import annotations

import base64
import binascii
import html
import json
from datetime import UTC, datetime
from json import JSONDecodeError

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from mongodb_vector_test_ui.chunking.service import chunk_text
from mongodb_vector_test_ui.core.config import (
    get_settings,
    safe_diagnostics,
    validate_settings,
    with_mongodb_target,
)
from mongodb_vector_test_ui.embeddings.providers import embed_documents, embed_query
from mongodb_vector_test_ui.ingestion.documents import (
    SUPPORTED_EXTENSIONS,
    extract_from_bytes,
    extract_from_path,
)
from mongodb_vector_test_ui.llm.answering import synthesize_answer
from mongodb_vector_test_ui.llm.providers import safe_model_diagnostics
from mongodb_vector_test_ui.retrieval.rerankers import (
    create_reranker,
    safe_reranker_diagnostics,
)
from mongodb_vector_test_ui.vectorstore.mongodb import MongoVectorStore


async def home(request: Request) -> HTMLResponse:
    settings = get_settings()
    return HTMLResponse(_render_page(settings))


async def status(request: Request) -> JSONResponse:
    try:
        settings = _target_settings_from_query(request)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    payload = {
        "timestamp": _now(),
        "config": _safe_config(settings),
        "config_issues": validate_settings(settings),
        "mongo_ok": False,
        "document_count": None,
        "indexes": [],
        "error": None,
    }
    try:
        store = MongoVectorStore(settings)
        payload["mongo_ok"] = store.ping()
        payload["document_count"] = store.count_documents()
        payload["indexes"] = store.list_vector_indexes()
    except Exception as exc:  # noqa: BLE001 - UI status should return diagnostics, not crash.
        payload["error"] = str(exc)
    return JSONResponse(payload)


async def mongodb_databases(request: Request) -> JSONResponse:
    settings = get_settings()
    try:
        store = MongoVectorStore(settings)
        return JSONResponse({"databases": store.list_databases()})
    except Exception as exc:  # noqa: BLE001 - Surface MongoDB browsing errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def mongodb_collections(request: Request) -> JSONResponse:
    try:
        settings = _target_settings_from_query(request, require_collection=False)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    try:
        store = MongoVectorStore(settings)
        return JSONResponse(
            {"database": settings.mongodb_db, "collections": store.list_collections(settings.mongodb_db)}
        )
    except Exception as exc:  # noqa: BLE001 - Surface MongoDB browsing errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def mongodb_collection_summary(request: Request) -> JSONResponse:
    try:
        settings = _target_settings_from_query(request)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    try:
        store = MongoVectorStore(settings)
        return JSONResponse({"summary": store.collection_summary()})
    except Exception as exc:  # noqa: BLE001 - Surface MongoDB browsing errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def create_index(request: Request) -> JSONResponse:
    try:
        payload = await _json_or_empty(request)
        settings = _target_settings_from_payload(payload)
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    try:
        store = MongoVectorStore(settings)
        result = store.ensure_vector_index()
        result["indexes"] = store.list_vector_indexes()
        return JSONResponse(result)
    except Exception as exc:  # noqa: BLE001 - Surface database/index errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def extract_uploaded_document(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)

    filename = str(payload.get("filename", "")).strip()
    encoded = str(payload.get("content_base64", "")).strip()
    if not filename:
        return JSONResponse({"error": "filename is required."}, status_code=422)
    if not encoded:
        return JSONResponse({"error": "content_base64 is required."}, status_code=422)

    try:
        data = base64.b64decode(encoded, validate=True)
        document = extract_from_bytes(data, filename=filename)
        return JSONResponse({"document": document.to_dict()})
    except (binascii.Error, ValueError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except Exception as exc:  # noqa: BLE001 - Surface extraction errors as JSON for the UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def extract_path_document(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)

    file_path = str(payload.get("file_path", "")).strip()
    if not file_path:
        return JSONResponse({"error": "file_path is required."}, status_code=422)

    try:
        document = extract_from_path(file_path)
        return JSONResponse({"document": document.to_dict()})
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except Exception as exc:  # noqa: BLE001 - Surface local file extraction errors as JSON.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def preview_chunks(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)

    title = str(payload.get("title", "Test document")).strip() or "Test document"
    source_id = str(payload.get("source_id", "")).strip() or _slug(title)
    text = str(payload.get("text", "")).strip()
    if len(text) < 20:
        return JSONResponse({"error": "Document text must contain at least 20 characters."}, status_code=422)

    chunks = chunk_text(source_id, title, text)
    previews = [
        {
            "chunk_id": chunk["chunk_id"],
            "source_id": chunk["source_id"],
            "metadata": chunk["metadata"],
            "characters": len(chunk["text"]),
            "text": chunk["text"],
        }
        for chunk in chunks
    ]
    return JSONResponse({"source_id": source_id, "title": title, "chunk_count": len(chunks), "chunks": previews})


async def index_document(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)

    title = str(payload.get("title", "Test document")).strip() or "Test document"
    source_id = str(payload.get("source_id", "")).strip() or _slug(title)
    text = str(payload.get("text", "")).strip()
    if len(text) < 20:
        return JSONResponse({"error": "Paste at least 20 characters of document text."}, status_code=422)

    try:
        settings = _target_settings_from_payload(payload)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    try:
        chunks = chunk_text(source_id, title, text)
        vectors = embed_documents([chunk["text"] for chunk in chunks], settings)
        store = MongoVectorStore(settings)
        inserted = store.replace_source_chunks(source_id, chunks, vectors)
        index_result = store.ensure_vector_index()
        return JSONResponse(
            {
                "source_id": source_id,
                "title": title,
                "chunks_created": len(chunks),
                "embeddings_created": len(vectors),
                "inserted": inserted,
                "embedding_provider": settings.embedding_provider,
                "embedding_model": _embedding_model(settings),
                "mongodb_db": settings.mongodb_db,
                "mongodb_collection": settings.mongodb_collection,
                "vector_index": settings.vector_index_name,
                "index_result": index_result,
            }
        )
    except Exception as exc:  # noqa: BLE001 - Surface embedding/database errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def search(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)

    query = str(payload.get("query", "")).strip()
    top_k = _top_k(payload.get("top_k", 5))
    min_score = _min_score(payload.get("min_score", 0.6))
    exact = _bool(payload.get("exact", False))
    num_candidates = _num_candidates(payload.get("num_candidates"), top_k=top_k, exact=exact)
    filters = _search_filters(payload)
    if len(query) < 2:
        return JSONResponse({"error": "Query must be at least 2 characters."}, status_code=422)

    try:
        settings = _target_settings_from_payload(payload)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    try:
        query_vector = embed_query(query, settings)
        store = MongoVectorStore(settings)
        available_filter_paths = store.vector_index_filter_paths()
        unsupported_filters = sorted(set(filters) - available_filter_paths)
        if unsupported_filters:
            return JSONResponse(
                {
                    "error": "Selected filter fields are not available on this vector index. Run Create / Check Index to inspect missing filter paths, then update or recreate the Atlas vector index if needed.",
                    "unsupported_filter_paths": unsupported_filters,
                    "available_filter_paths": sorted(available_filter_paths),
                    "filters": filters,
                    "mongodb_db": settings.mongodb_db,
                    "mongodb_collection": settings.mongodb_collection,
                    "vector_index": settings.vector_index_name,
                },
                status_code=422,
            )
        results = store.vector_search(
            query_vector,
            top_k=top_k,
            min_score=min_score,
            num_candidates=num_candidates,
            exact=exact,
            filters=filters,
        )
        return JSONResponse(
            {
                "query": query,
                "top_k": top_k,
                "min_score": min_score,
                "num_candidates": num_candidates,
                "exact": exact,
                "filters": filters,
                "embedding_provider": settings.embedding_provider,
                "embedding_model": _embedding_model(settings),
                "mongodb_db": settings.mongodb_db,
                "mongodb_collection": settings.mongodb_collection,
                "result_count": len(results),
                "results": results,
            }
        )
    except Exception as exc:  # noqa: BLE001 - Surface embedding/database errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def rerank(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)

    question = str(payload.get("question") or payload.get("query") or "").strip()
    candidates = payload.get("candidates")
    if len(question) < 2:
        return JSONResponse({"error": "Question must be at least 2 characters."}, status_code=422)
    if not isinstance(candidates, list) or not candidates:
        return JSONResponse({"error": "Candidates must be a non-empty list."}, status_code=422)
    if len(candidates) > 1000:
        return JSONResponse({"error": "Candidates cannot exceed 1000 items."}, status_code=422)
    if any(not isinstance(candidate, dict) for candidate in candidates):
        return JSONResponse({"error": "Every candidate must be a JSON object."}, status_code=422)

    try:
        results = create_reranker().rerank(question, candidates, top_k=None)
        diagnostics = safe_reranker_diagnostics()
        return JSONResponse(
            {
                "question": question,
                "candidate_count": len(candidates),
                "result_count": len(results),
                "return_all": True,
                "rerank_provider": diagnostics["rerank_provider"],
                "rerank_model": diagnostics["rerank_model"],
                "results": results,
            }
        )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except Exception as exc:  # noqa: BLE001 - Surface provider errors in the test UI.
        return JSONResponse({"error": str(exc)}, status_code=500)


async def ask(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return JSONResponse({"error": "Request body must be valid JSON."}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "Request body must be a JSON object."}, status_code=400)

    query = str(payload.get("query", "")).strip()
    if len(query) < 2:
        return JSONResponse({"error": "Query must be at least 2 characters."}, status_code=422)
    try:
        settings = _target_settings_from_payload(payload)
        top_k = _top_k(payload.get("top_k", 10))
        min_score = _min_score(payload.get("min_score", 0.6))
        exact = _bool(payload.get("exact", False))
        num_candidates = _num_candidates(payload.get("num_candidates"), top_k, exact)
        filters = _search_filters(payload)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)

    try:
        query_vector = embed_query(query, settings)
        store = MongoVectorStore(settings)
        available_paths = store.vector_index_filter_paths()
        unsupported = sorted(set(filters) - available_paths)
        if unsupported:
            return JSONResponse(
                {
                    "error": "Selected filters are not available on the active vector index.",
                    "unsupported_filter_paths": unsupported,
                    "available_filter_paths": sorted(available_paths),
                },
                status_code=422,
            )
        candidates = store.vector_search(
            query_vector, top_k=top_k, min_score=min_score,
            num_candidates=num_candidates, exact=exact, filters=filters,
        )
    except Exception as exc:  # noqa: BLE001 - Keep retrieval failures in the API contract.
        return JSONResponse({"error": str(exc)}, status_code=500)

    if not candidates:
        return JSONResponse(
            {
                "query": query,
                "answer": "The indexed sources do not contain enough information to answer this question.",
                "citations": [], "insufficient_evidence": True,
                "candidate_count": 0, "reranked_count": 0, "evidence_count": 0,
                "results": [], "evidence": [],
                "mongodb_db": settings.mongodb_db,
                "mongodb_collection": settings.mongodb_collection,
            }
        )

    try:
        result = synthesize_answer(query, candidates, settings=settings)
        model_info = safe_model_diagnostics()
        rerank_info = safe_reranker_diagnostics(settings)
        return JSONResponse(
            {
                "query": query, **result,
                "embedding_provider": settings.embedding_provider,
                "embedding_model": _embedding_model(settings),
                "rerank_provider": rerank_info["rerank_provider"],
                "rerank_model": rerank_info["rerank_model"],
                "chat_provider": model_info.get("chat_provider"),
                "chat_model": model_info.get("chat_model"),
                "mongodb_db": settings.mongodb_db,
                "mongodb_collection": settings.mongodb_collection,
            }
        )
    except (ValueError, RuntimeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)
    except Exception as exc:  # noqa: BLE001 - Surface model-provider failures as JSON.
        return JSONResponse({"error": str(exc)}, status_code=502)


def _safe_config(settings) -> dict:
    diagnostics = safe_diagnostics(settings)
    diagnostics["embedding_model"] = _embedding_model(settings)
    diagnostics.update(safe_model_diagnostics())
    diagnostics.update(safe_reranker_diagnostics(settings))
    return diagnostics


async def _json_or_empty(request: Request) -> dict:
    if not (await request.body()):
        return {}
    return await request.json()


def _target_settings_from_query(request: Request, require_collection: bool = True):
    settings = get_settings()
    database = str(request.query_params.get("database", settings.mongodb_db)).strip()
    collection = str(request.query_params.get("collection", settings.mongodb_collection)).strip()
    if not require_collection and not collection:
        collection = settings.mongodb_collection
    return with_mongodb_target(settings, database=database, collection=collection)


def _target_settings_from_payload(payload: dict):
    settings = get_settings()
    database = str(payload.get("mongodb_db", settings.mongodb_db)).strip()
    collection = str(payload.get("mongodb_collection", settings.mongodb_collection)).strip()
    return with_mongodb_target(settings, database=database, collection=collection)


def _embedding_model(settings) -> str:
    if settings.embedding_provider == "voyage":
        return settings.voyage_model
    if settings.embedding_provider == "openai":
        return settings.openai_embedding_model
    return "deterministic hashing"


def _top_k(value: object) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 5
    return min(max(parsed, 1), 50)


def _num_candidates(value: object, top_k: int, exact: bool) -> int | None:
    if exact:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = max(get_settings().vector_num_candidates, top_k * 20)
    return min(max(parsed, top_k), 10000)


def _min_score(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = 0.6
    return min(max(parsed, 0.0), 1.0)


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _search_filters(payload: dict) -> dict:
    fields = {
        "metadata.source_id": str(payload.get("source_id_filter", "")).strip(),
        "metadata.title": str(payload.get("title_filter", "")).strip(),
        "metadata.section": str(payload.get("section_filter", "")).strip(),
        "chunk_id": str(payload.get("chunk_id_filter", "")).strip(),
    }
    return {field: value for field, value in fields.items() if value}


def _slug(value: str) -> str:
    chars = [c.lower() if c.isalnum() else "-" for c in value]
    return "-".join(part for part in "".join(chars).split("-") if part)[:80] or "test-document"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _render_page(settings) -> str:
    config_json = html.escape(json.dumps(_safe_config(settings), indent=2))
    default_target_json = json.dumps(
        {"mongodb_db": settings.mongodb_db, "mongodb_collection": settings.mongodb_collection}
    )
    supported_extensions = ", ".join(SUPPORTED_EXTENSIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MongoDB Vector Search Test UI</title>
  <style>
    :root {{
      --bg: #0e1116;
      --panel: #151a22;
      --panel-2: #1d2430;
      --text: #ecf2ff;
      --muted: #9ca9bd;
      --line: #2e3848;
      --cyan: #39d5ff;
      --green: #50e3a4;
      --amber: #f6c15f;
      --red: #ff6b7a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 20px;
    }}
    h1 {{ margin: 0 0 6px; font-size: clamp(1.8rem, 3vw, 3rem); }}
    p {{ color: var(--muted); line-height: 1.55; }}
    code, pre {{ font-family: Consolas, Monaco, monospace; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }}
    .wide {{ grid-column: 1 / -1; }}
    .row {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .stack {{ display: grid; gap: 10px; }}
    label {{ display: block; color: var(--muted); font-size: 0.82rem; margin-bottom: 6px; }}
    input, textarea, select {{
      width: 100%;
      color: var(--text);
      background: #0b0f15;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 12px;
      outline: none;
    }}
    input[type="file"] {{ display: none; }}
    textarea {{ min-height: 220px; resize: vertical; }}
    button {{
      background: var(--cyan);
      color: #041018;
      border: 0;
      border-radius: 6px;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
    }}
    button.secondary {{ background: var(--panel-2); color: var(--text); border: 1px solid var(--line); }}
    button:disabled {{ opacity: 0.55; cursor: wait; }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      background: var(--panel-2);
      color: var(--muted);
      border: 1px solid var(--line);
      white-space: nowrap;
    }}
    .dot {{ width: 9px; height: 9px; border-radius: 50%; background: var(--amber); }}
    .dot.ok {{ background: var(--green); }}
    .dot.bad {{ background: var(--red); }}
    pre {{
      overflow: auto;
      max-height: 380px;
      background: #0b0f15;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      color: #dce7f8;
      line-height: 1.45;
    }}
    .cards {{ display: grid; gap: 10px; }}
    .result {{
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-left: 3px solid var(--cyan);
      border-radius: 8px;
      padding: 12px;
    }}
    .score {{ color: var(--green); font-weight: 700; }}
    .muted {{ color: var(--muted); }}
    .target {{
      display: inline-flex;
      gap: 6px;
      align-items: center;
      color: var(--muted);
      font-size: 0.86rem;
    }}
    .target strong {{ color: var(--text); }}
    .check {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .check input {{ width: auto; }}
    .dropzone {{
      display: grid;
      place-items: center;
      min-height: 116px;
      padding: 16px;
      background: #0b0f15;
      border: 1px dashed var(--line);
      border-radius: 8px;
      color: var(--muted);
      text-align: center;
      cursor: pointer;
    }}
    .dropzone.dragover {{
      border-color: var(--cyan);
      color: var(--text);
      background: rgba(57, 213, 255, 0.08);
    }}
    .mini {{
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 0.82rem;
    }}
    @media (max-width: 820px) {{
      header, .grid {{ grid-template-columns: 1fr; display: grid; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>MongoDB Vector Search Test UI</h1>
      <p>Index a small document, create/check the vector index, and run semantic search using the same embedding path as the Profile Agent.</p>
    </div>
    <div class="status"><span id="status-dot" class="dot"></span><span id="status-text">Checking MongoDB</span></div>
  </header>

  <section class="grid">
    <div class="panel">
      <h2>Runtime Config</h2>
      <pre id="config">{config_json}</pre>
      <div class="row">
        <button id="refresh" class="secondary">Refresh Status</button>
        <button id="create-index">Create / Check Index</button>
      </div>
    </div>

    <div class="panel">
      <h2>Status</h2>
      <pre id="status-output">Waiting...</pre>
    </div>

    <div class="panel wide">
      <h2>MongoDB Browser</h2>
      <p class="mini">Select a database and collection to test without editing `.env`.</p>
      <div class="grid">
        <div>
          <label for="database-select">Database</label>
          <select id="database-select">
            <option value="{html.escape(settings.mongodb_db)}">{html.escape(settings.mongodb_db)}</option>
          </select>
        </div>
        <div>
          <label for="collection-select">Collection</label>
          <select id="collection-select">
            <option value="{html.escape(settings.mongodb_collection)}">{html.escape(settings.mongodb_collection)}</option>
          </select>
        </div>
      </div>
      <div class="row">
        <button id="load-databases" class="secondary">Load Databases</button>
        <button id="load-collections" class="secondary">Load Collections</button>
        <button id="inspect-collection">Inspect Collection</button>
        <span class="target">Active target: <strong id="active-target">{html.escape(settings.mongodb_db)}.{html.escape(settings.mongodb_collection)}</strong></span>
      </div>
      <pre id="browser-output">No database browser run yet.</pre>
    </div>

    <div class="panel wide">
      <h2>Document Ingestion</h2>
      <div class="grid">
        <div class="stack">
          <div>
            <label for="file-path">Local File Path</label>
            <input id="file-path" placeholder="C:\\path\\to\\document.pdf">
          </div>
          <div class="row">
            <button id="load-path" class="secondary">Extract From Path</button>
          </div>
        </div>
        <div class="stack">
          <label for="file-input">Upload Or Drop</label>
          <div id="dropzone" class="dropzone" role="button" tabindex="0">
            <span>Drop TXT, PDF, DOCX or choose file</span>
          </div>
          <input id="file-input" type="file" accept="{supported_extensions}">
          <p class="mini">Supported: {html.escape(supported_extensions)}</p>
        </div>
      </div>
      <pre id="extract-output">No document extracted yet.</pre>
    </div>

    <div class="panel wide">
      <h2>Review, Chunk, Embed, Store</h2>
      <div class="grid">
        <div>
          <label for="title">Title</label>
          <input id="title" value="Profile Agent Test Document">
        </div>
        <div>
          <label for="source-id">Source ID</label>
          <input id="source-id" value="profile-agent-test">
        </div>
      </div>
      <label for="doc-text">Document Text</label>
      <textarea id="doc-text">Jabulani is building a Profile Agent that uses MongoDB Vector Search and Voyage embeddings. The assistant should answer questions about his data engineering, AI systems, analytics projects, and portfolio work using retrieved source context.</textarea>
      <div class="row">
        <button id="preview-chunks" class="secondary">Preview Chunks</button>
        <button id="index-doc">Chunk, Embed, and Store</button>
      </div>
      <pre id="chunk-output">No chunk preview yet.</pre>
      <pre id="index-output">No indexing run yet.</pre>
    </div>

    <div class="panel wide">
      <h2>Vector Search</h2>
      <div class="grid">
        <div>
          <label for="query">Question / Query</label>
          <input id="query" value="What is the Profile Agent using MongoDB for?">
        </div>
        <div>
          <label for="top-k">Top K Results</label>
          <input id="top-k" type="number" min="1" max="50" value="5">
        </div>
        <div>
          <label for="min-score">Minimum Similarity Score</label>
          <input id="min-score" type="number" min="0" max="1" step="0.05" value="0.6">
        </div>
        <div>
          <label for="num-candidates">numCandidates</label>
          <input id="num-candidates" type="number" min="1" max="10000" value="{settings.vector_num_candidates}">
        </div>
        <div>
          <label for="source-id-filter">Source ID Filter</label>
          <input id="source-id-filter" placeholder="document-ingestion-smoke-test">
        </div>
        <div>
          <label for="title-filter">Title Filter</label>
          <input id="title-filter" placeholder="Master Career Profile">
        </div>
        <div>
          <label for="section-filter">Section Filter</label>
          <input id="section-filter" placeholder="Projects, Experience, Skills">
        </div>
        <div>
          <label for="chunk-id-filter">Chunk ID Filter</label>
          <input id="chunk-id-filter" placeholder="Known chunk id for diagnostics">
        </div>
        <div class="stack">
          <label>Search Mode</label>
          <label class="check"><input id="exact-search" type="checkbox"> Exact nearest-neighbor search</label>
        </div>
      </div>
      <p class="mini">Results below `0.6` similarity are hidden by default. Use exact mode mainly as a quality benchmark; normal ANN search is usually better for responsive retrieval.</p>
      <div class="row">
        <button id="search">Embed Query, Search, and Rerank</button>
      </div>
      <div id="results" class="cards"></div>
      <pre id="search-output">No search run yet.</pre>
    </div>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
const defaultTarget = {default_target_json};

async function callJson(url, options = {{}}) {{
  const response = await fetch(url, {{
    headers: {{ "Content-Type": "application/json", ...(options.headers || {{}}) }},
    ...options
  }});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || data.detail || JSON.stringify(data));
  return data;
}}

function pretty(value) {{
  return JSON.stringify(value, null, 2);
}}

function setBusy(button, busy) {{
  button.disabled = busy;
}}

async function refreshStatus() {{
  try {{
    const data = await callJson(`/api/status?${{targetQuery()}}`);
    $("status-output").textContent = pretty(data);
    $("status-dot").className = "dot " + (data.mongo_ok ? "ok" : "bad");
    $("status-text").textContent = data.mongo_ok ? `MongoDB OK - ${{data.document_count}} docs` : "MongoDB issue";
  }} catch (error) {{
    $("status-output").textContent = String(error);
    $("status-dot").className = "dot bad";
    $("status-text").textContent = "Status failed";
  }}
}}

async function loadDatabases() {{
  const button = $("load-databases");
  setBusy(button, true);
  try {{
    const data = await callJson("/api/mongodb/databases");
    fillSelect($("database-select"), data.databases.map((item) => item.name), selectedDatabase());
    $("browser-output").textContent = pretty(data);
    await loadCollections();
  }} catch (error) {{
    $("browser-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function loadCollections() {{
  const button = $("load-collections");
  setBusy(button, true);
  try {{
    const data = await callJson(`/api/mongodb/collections?database=${{encodeURIComponent(selectedDatabase())}}`);
    fillSelect($("collection-select"), data.collections.map((item) => item.name), selectedCollection());
    $("browser-output").textContent = pretty(data);
    updateActiveTarget();
  }} catch (error) {{
    $("browser-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function inspectCollection() {{
  const button = $("inspect-collection");
  setBusy(button, true);
  try {{
    const data = await callJson(`/api/mongodb/collection/summary?${{targetQuery()}}`);
    $("browser-output").textContent = pretty(data);
    await refreshStatus();
  }} catch (error) {{
    $("browser-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function createIndex() {{
  const button = $("create-index");
  setBusy(button, true);
  try {{
    const data = await callJson("/api/index/create", {{
      method: "POST",
      body: JSON.stringify(selectedTarget())
    }});
    $("status-output").textContent = pretty(data);
    await refreshStatus();
  }} catch (error) {{
    $("status-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function extractFromPath() {{
  const button = $("load-path");
  setBusy(button, true);
  try {{
    const data = await callJson("/api/document/extract/path", {{
      method: "POST",
      body: JSON.stringify({{ file_path: $("file-path").value }})
    }});
    applyExtractedDocument(data.document);
  }} catch (error) {{
    $("extract-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function extractUpload(file) {{
  if (!file) return;
  $("extract-output").textContent = `Reading ${{file.name}}...`;
  try {{
    const buffer = await file.arrayBuffer();
    const data = await callJson("/api/document/extract/upload", {{
      method: "POST",
      body: JSON.stringify({{
        filename: file.name,
        content_base64: arrayBufferToBase64(buffer)
      }})
    }});
    applyExtractedDocument(data.document);
  }} catch (error) {{
    $("extract-output").textContent = String(error);
  }}
}}

function applyExtractedDocument(document) {{
  $("title").value = document.title || document.filename || "Document";
  $("source-id").value = document.source_id || slug($("title").value);
  $("doc-text").value = document.text || "";
  $("chunk-output").textContent = "No chunk preview yet.";
  $("index-output").textContent = "No indexing run yet.";
  $("extract-output").textContent = pretty({{
    filename: document.filename,
    extension: document.extension,
    title: document.title,
    source_id: document.source_id,
    characters: document.characters,
    source_path: document.source_path || "",
    text_preview: (document.text || "").slice(0, 900)
  }});
}}

async function previewChunks() {{
  const button = $("preview-chunks");
  setBusy(button, true);
  try {{
    const data = await callJson("/api/document/chunks", {{
      method: "POST",
      body: JSON.stringify({{
        title: $("title").value,
        source_id: $("source-id").value,
        text: $("doc-text").value,
        ...selectedTarget()
      }})
    }});
    $("chunk-output").textContent = pretty(data);
  }} catch (error) {{
    $("chunk-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function indexDocument() {{
  const button = $("index-doc");
  setBusy(button, true);
  try {{
    const data = await callJson("/api/index/document", {{
      method: "POST",
      body: JSON.stringify({{
        title: $("title").value,
        source_id: $("source-id").value,
        text: $("doc-text").value,
        ...selectedTarget()
      }})
    }});
    $("index-output").textContent = pretty(data);
    await refreshStatus();
  }} catch (error) {{
    $("index-output").textContent = String(error);
  }} finally {{
    setBusy(button, false);
  }}
}}

async function search() {{
  const button = $("search");
  setBusy(button, true);
  try {{
    const searchData = await callJson("/api/search", {{
      method: "POST",
      body: JSON.stringify({{
        query: $("query").value,
        top_k: $("top-k").value,
        min_score: $("min-score").value,
        num_candidates: $("num-candidates").value,
        exact: $("exact-search").checked,
        source_id_filter: $("source-id-filter").value,
        title_filter: $("title-filter").value,
        section_filter: $("section-filter").value,
        chunk_id_filter: $("chunk-id-filter").value,
        ...selectedTarget()
      }})
    }});
    const rerankData = searchData.results.length
      ? await callJson("/api/rerank", {{
          method: "POST",
          body: JSON.stringify({{
            question: searchData.query,
            candidates: searchData.results
          }})
        }})
      : {{
          question: searchData.query,
          candidate_count: 0,
          result_count: 0,
          results: []
        }};
    $("search-output").textContent = pretty({{
      search: searchData,
      rerank: rerankData
    }});
    $("results").innerHTML = rerankData.results.map((item) => `
      <article class="result">
        <div>
          <span class="score">vector ${{Number(item.vector_score ?? item.score ?? 0).toFixed(4)}}</span>
          <span class="score">rerank ${{Number(item.rerank_score ?? 0).toFixed(4)}}</span>
          <span class="muted">${{escapeHtml(item.metadata?.title || item.source_id || "document")}}</span>
        </div>
        <div class="mini">source_id: ${{escapeHtml(item.source_id || "")}} | chunk_id: ${{escapeHtml(item.chunk_id || "")}}</div>
        <p>${{escapeHtml((item.text || "").slice(0, 650))}}</p>
      </article>
    `).join("");
  }} catch (error) {{
    $("search-output").textContent = String(error);
    $("results").innerHTML = "";
  }} finally {{
    setBusy(button, false);
  }}
}}

function escapeHtml(value) {{
  return value.replace(/[&<>"']/g, (char) => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }}[char]));
}}

function arrayBufferToBase64(buffer) {{
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {{
    const chunk = bytes.subarray(offset, offset + chunkSize);
    binary += String.fromCharCode(...chunk);
  }}
  return btoa(binary);
}}

function slug(value) {{
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "document";
}}

function selectedDatabase() {{
  return $("database-select").value || defaultTarget.mongodb_db;
}}

function selectedCollection() {{
  return $("collection-select").value || defaultTarget.mongodb_collection;
}}

function selectedTarget() {{
  return {{
    mongodb_db: selectedDatabase(),
    mongodb_collection: selectedCollection()
  }};
}}

function targetQuery() {{
  const target = selectedTarget();
  return new URLSearchParams({{ database: target.mongodb_db, collection: target.mongodb_collection }}).toString();
}}

function updateActiveTarget() {{
  $("active-target").textContent = `${{selectedDatabase()}}.${{selectedCollection()}}`;
}}

function fillSelect(select, values, preferred) {{
  const unique = [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
  if (!unique.includes(preferred)) unique.unshift(preferred);
  select.innerHTML = unique.map((value) => `<option value="${{escapeHtml(value)}}">${{escapeHtml(value)}}</option>`).join("");
  select.value = preferred;
  updateActiveTarget();
}}

$("refresh").addEventListener("click", refreshStatus);
$("create-index").addEventListener("click", createIndex);
$("load-databases").addEventListener("click", loadDatabases);
$("load-collections").addEventListener("click", loadCollections);
$("inspect-collection").addEventListener("click", inspectCollection);
$("database-select").addEventListener("change", () => {{
  updateActiveTarget();
  loadCollections();
}});
$("collection-select").addEventListener("change", updateActiveTarget);
$("load-path").addEventListener("click", extractFromPath);
$("dropzone").addEventListener("click", () => $("file-input").click());
$("dropzone").addEventListener("keydown", (event) => {{
  if (event.key === "Enter" || event.key === " ") {{
    event.preventDefault();
    $("file-input").click();
  }}
}});
$("file-input").addEventListener("change", (event) => extractUpload(event.target.files[0]));
for (const eventName of ["dragenter", "dragover"]) {{
  $("dropzone").addEventListener(eventName, (event) => {{
    event.preventDefault();
    $("dropzone").classList.add("dragover");
  }});
}}
for (const eventName of ["dragleave", "drop"]) {{
  $("dropzone").addEventListener(eventName, (event) => {{
    event.preventDefault();
    $("dropzone").classList.remove("dragover");
  }});
}}
$("dropzone").addEventListener("drop", (event) => extractUpload(event.dataTransfer.files[0]));
$("preview-chunks").addEventListener("click", previewChunks);
$("index-doc").addEventListener("click", indexDocument);
$("search").addEventListener("click", search);
updateActiveTarget();
refreshStatus();
</script>
</body>
</html>"""


app = Starlette(
    debug=get_settings().app_env == "local",
    routes=[
        Route("/", home, methods=["GET"]),
        Route("/api/status", status, methods=["GET"]),
        Route("/api/mongodb/databases", mongodb_databases, methods=["GET"]),
        Route("/api/mongodb/collections", mongodb_collections, methods=["GET"]),
        Route("/api/mongodb/collection/summary", mongodb_collection_summary, methods=["GET"]),
        Route("/api/index/create", create_index, methods=["POST"]),
        Route("/api/document/extract/upload", extract_uploaded_document, methods=["POST"]),
        Route("/api/document/extract/path", extract_path_document, methods=["POST"]),
        Route("/api/document/chunks", preview_chunks, methods=["POST"]),
        Route("/api/index/document", index_document, methods=["POST"]),
        Route("/api/search", search, methods=["POST"]),
        Route("/api/rerank", rerank, methods=["POST"]),
        Route("/api/ask", ask, methods=["POST"]),
    ],
)
