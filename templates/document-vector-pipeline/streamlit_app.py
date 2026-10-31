from __future__ import annotations

import base64
import os
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:8765").rstrip("/")
DEFAULT_DATABASE = os.getenv("RAG_TEST_DATABASE", "RAG_with_MongoDB")
DEFAULT_COLLECTION = os.getenv("RAG_TEST_COLLECTION", "profile_chunks")


class ApiError(RuntimeError):
    """Readable RAG API failure."""


def api_request(
    method: str,
    base_url: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 45,
) -> dict[str, Any]:
    try:
        response = requests.request(
            method,
            f"{base_url.rstrip('/')}{path}",
            params=params,
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach the RAG API: {exc}") from exc
    try:
        data = response.json()
    except requests.JSONDecodeError as exc:
        raise ApiError(f"HTTP {response.status_code} returned without JSON.") from exc
    if not response.ok:
        detail = data.get("error") or data.get("detail") or data
        raise ApiError(f"HTTP {response.status_code}: {detail}")
    return data


def item_names(items: list[dict[str, Any]]) -> list[str]:
    return [item["name"] for item in items if item.get("name")]


def apply_document(document: dict[str, Any]) -> None:
    st.session_state.extracted_document = document
    st.session_state.document_title = document.get("title") or "Document"
    st.session_state.document_source_id = document.get("source_id") or "document"
    st.session_state.document_text = document.get("text") or ""
    st.session_state.pop("chunk_preview", None)
    st.session_state.pop("index_result", None)


def render_result(result: dict[str, Any], rank: int) -> None:
    metadata = result.get("metadata") or {}
    title = result.get("title") or metadata.get("title") or result.get("source_id") or "Untitled source"
    vector_score = float(result.get("vector_score", result.get("score")) or 0)
    rerank_score = result.get("rerank_score")
    source_id = result.get("source_id") or metadata.get("source_id") or "Unknown"
    section = result.get("section") or metadata.get("section") or "Unspecified"
    with st.container(border=True):
        heading, vector_metric, rerank_metric = st.columns([4, 1, 1])
        heading.markdown(f"**{rank}. {title}**")
        vector_metric.metric("Vector", f"{vector_score:.3f}")
        rerank_metric.metric(
            "Rerank",
            f"{float(rerank_score):.3f}" if rerank_score is not None else "Not run",
        )
        st.write(result.get("text") or "No chunk text returned.")
        st.caption(
            f"Source: {source_id} | Chunk: {result.get('chunk_id') or 'Unknown'} | "
            f"Section: {section}"
        )


def render_search_response(message: dict[str, Any]) -> None:
    st.markdown(message["content"])
    if message.get("answer"):
        st.markdown("#### Grounded answer")
        st.write(message["answer"])
        if message.get("citations"):
            st.markdown("**Cited sources**")
            for citation in message["citations"]:
                st.caption(
                    f"[{citation.get('evidence_id')}] {citation.get('title') or citation.get('source_id')} "
                    f"| source: {citation.get('source_id')} | chunk: {citation.get('chunk_id')} "
                    f"| vector: {citation.get('vector_score')} | rerank: {citation.get('rerank_score')}"
                )
        if message.get("insufficient_evidence"):
            st.warning("The retrieved evidence was insufficient for a supported answer.")
    results = message.get("reranked_results") or message.get("results", [])
    if message.get("reranked_results") is not None:
        st.success(f"Reranked all {len(results)} retrieved candidates.")
    elif results:
        st.info(
            "Vector search completed, but reranking has not completed. Use the retry "
            "button below to request Voyage reranking."
        )
    if message.get("rerank_error"):
        st.error(f"Reranking failed: {message['rerank_error']}")
    for rank, result in enumerate(results, start=1):
        render_result(result, rank)
    if message.get("response"):
        with st.expander("Raw /api/search response"):
            st.json(message["response"])
    if message.get("rerank_response"):
        with st.expander("Raw /api/rerank response"):
            st.json(message["rerank_response"])


def rerank_search_message(api_url: str, message: dict[str, Any]) -> None:
    response = api_request(
        "POST",
        api_url,
        "/api/rerank",
        payload={
            "question": message.get("query", ""),
            "candidates": message.get("results", []),
        },
        timeout=120,
    )
    message["reranked_results"] = response.get("results", [])
    message["rerank_response"] = response


st.set_page_config(
    page_title="Reusable MongoDB RAG Retrieval Lab",
    page_icon=":material/search:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Reusable MongoDB RAG Retrieval Lab")
st.caption("Independent Streamlit client for the FastAPI MongoDB RAG service.")

status: dict[str, Any] | None = None
with st.sidebar:
    st.header("MongoDB connection")
    api_url = st.text_input("RAG API URL", value=DEFAULT_API_URL)
    status_slot = st.empty()

    st.subheader("Database")
    database_options = st.session_state.get("databases", [DEFAULT_DATABASE])
    if DEFAULT_DATABASE not in database_options:
        database_options = [DEFAULT_DATABASE, *database_options]
    database = st.selectbox("Database", database_options, label_visibility="collapsed")
    if st.button(
        "Load MongoDB targets", icon=":material/database:", use_container_width=True
    ):
        try:
            response = api_request("GET", api_url, "/api/mongodb/databases")
            st.session_state.databases = item_names(response.get("databases", []))
            st.session_state.pop("collections", None)
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))

    st.subheader("Collection")
    collection_options = st.session_state.get("collections", [DEFAULT_COLLECTION])
    if DEFAULT_COLLECTION not in collection_options:
        collection_options = [DEFAULT_COLLECTION, *collection_options]
    collection = st.selectbox(
        "Collection", collection_options, label_visibility="collapsed"
    )
    if st.button(
        "Load collections", icon=":material/folder_open:", use_container_width=True
    ):
        try:
            response = api_request(
                "GET",
                api_url,
                "/api/mongodb/collections",
                params={"database": database},
            )
            st.session_state.collections = item_names(response.get("collections", []))
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))

    st.caption("Active retrieval target")
    st.code(f"{database}.{collection}", language=None)

    target_params = {"database": database, "collection": collection}
    with status_slot.container():
        st.caption("API status")
        try:
            status = api_request("GET", api_url, "/api/status", params=target_params)
            if status.get("mongo_ok"):
                st.success(
                    f"Connected | {status.get('document_count', 0)} documents"
                )
            else:
                st.error(status.get("error") or "MongoDB status check failed.")
        except ApiError as exc:
            st.error(str(exc))

    st.divider()
    st.header("Retrieval controls")
    top_k = st.number_input("Top K", 1, 50, 5)
    min_score = st.slider("Minimum similarity", 0.0, 1.0, 0.6, 0.01)
    exact = st.toggle("Exact nearest-neighbor search", value=False)
    num_candidates = st.number_input(
        "numCandidates",
        min_value=int(top_k),
        max_value=10000,
        value=max(150, int(top_k)),
        disabled=exact,
    )
    with st.expander("Indexed filters", expanded=True):
        source_id_filter = st.text_input(
            "Source ID", placeholder="mvp1-template-smoke-test"
        )
        title_filter = st.text_input("Title")
        section_filter = st.text_input("Section")
        chunk_id_filter = st.text_input("Chunk ID")

st.subheader("API diagnostics")
with st.expander("Status response"):
    if status is not None:
        st.json(status)
    else:
        st.info("Start Starlette or correct the API URL to load status details.")

st.subheader("Collection inspection")
if st.button("Inspect collection", icon=":material/info:"):
    try:
        st.session_state.collection_summary = api_request(
            "GET",
            api_url,
            "/api/mongodb/collection/summary",
            params=target_params,
        )
    except ApiError as exc:
        st.error(str(exc))
if "collection_summary" in st.session_state:
    with st.expander("Collection summary", expanded=True):
        st.json(st.session_state.collection_summary)

st.divider()
st.subheader("Document ingestion test")
st.caption(
    "Extract a supported document through Starlette, review its text, preview chunks, "
    "then explicitly embed and store it in the active collection."
)
upload_tab, path_tab = st.tabs(["Upload or drop", "Local file path"])

with upload_tab:
    uploaded_file = st.file_uploader(
        "Drop a document here",
        type=["txt", "md", "markdown", "csv", "json", "log", "html", "htm", "docx", "pdf"],
        help="Maximum file size accepted by the Starlette extractor is 12 MB.",
    )
    if st.button(
        "Extract uploaded document",
        icon=":material/upload_file:",
        disabled=uploaded_file is None,
    ):
        try:
            encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
            with st.spinner("Extracting document text through Starlette..."):
                response = api_request(
                    "POST",
                    api_url,
                    "/api/document/extract/upload",
                    payload={
                        "filename": uploaded_file.name,
                        "content_base64": encoded,
                    },
                )
            apply_document(response["document"])
            st.success("Document extracted. Review the text below before continuing.")
        except (ApiError, KeyError) as exc:
            st.error(str(exc))

with path_tab:
    local_path = st.text_input(
        "Path on the Starlette server",
        placeholder=r"C:\path\to\document.pdf",
        help="This path must be readable by the machine running Starlette.",
    )
    if st.button(
        "Extract from path",
        icon=":material/folder_open:",
        disabled=not local_path.strip(),
    ):
        try:
            with st.spinner("Reading and extracting the server-side document..."):
                response = api_request(
                    "POST",
                    api_url,
                    "/api/document/extract/path",
                    payload={"file_path": local_path},
                )
            apply_document(response["document"])
            st.success("Document extracted. Review the text below before continuing.")
        except (ApiError, KeyError) as exc:
            st.error(str(exc))

if "extracted_document" in st.session_state:
    document = st.session_state.extracted_document
    st.caption(
        f"Extracted: {document.get('filename', 'document')} | "
        f"{document.get('characters', len(st.session_state.document_text))} characters | "
        f"Type: {document.get('extension', 'unknown')}"
    )
    identity_col, source_col = st.columns(2)
    with identity_col:
        st.text_input("Document title", key="document_title")
    with source_col:
        st.text_input(
            "Source ID",
            key="document_source_id",
            help="Re-ingesting this Source ID replaces its existing chunks.",
        )
    st.text_area(
        "Extracted document text",
        key="document_text",
        height=320,
        help="Edit or remove unwanted text before creating chunks and embeddings.",
    )

    preview_col, store_col = st.columns(2)
    with preview_col:
        if st.button(
            "Preview chunks",
            icon=":material/preview:",
            use_container_width=True,
        ):
            try:
                with st.spinner("Creating a preview without embeddings or writes..."):
                    st.session_state.chunk_preview = api_request(
                        "POST",
                        api_url,
                        "/api/document/chunks",
                        payload={
                            "title": st.session_state.document_title,
                            "source_id": st.session_state.document_source_id,
                            "text": st.session_state.document_text,
                        },
                    )
            except ApiError as exc:
                st.error(str(exc))
    with store_col:
        if st.button(
            "Chunk, embed, and store",
            icon=":material/save:",
            type="primary",
            use_container_width=True,
            help="Writes vectors to the active MongoDB collection.",
        ):
            try:
                with st.spinner("Chunking, embedding, and writing to MongoDB..."):
                    st.session_state.index_result = api_request(
                        "POST",
                        api_url,
                        "/api/index/document",
                        payload={
                            "mongodb_db": database,
                            "mongodb_collection": collection,
                            "title": st.session_state.document_title,
                            "source_id": st.session_state.document_source_id,
                            "text": st.session_state.document_text,
                        },
                        timeout=300,
                    )
                st.success(
                    f"Stored document in {database}.{collection}. "
                    "You can now query it below."
                )
            except ApiError as exc:
                st.error(str(exc))

    if "chunk_preview" in st.session_state:
        preview = st.session_state.chunk_preview
        st.markdown(f"**Chunk preview: {preview.get('chunk_count', 0)} chunks**")
        with st.expander("Review chunk text and metadata", expanded=True):
            for index, chunk in enumerate(preview.get("chunks", []), start=1):
                st.markdown(f"**Chunk {index}: `{chunk.get('chunk_id', '')}`**")
                st.write(chunk.get("text", ""))
                st.caption(f"{chunk.get('characters', 0)} characters")
                if index < len(preview.get("chunks", [])):
                    st.divider()
        with st.expander("Raw /api/document/chunks response"):
            st.json(preview)

    if "index_result" in st.session_state:
        result = st.session_state.index_result
        metric_cols = st.columns(3)
        metric_cols[0].metric("Chunks", result.get("chunks_created", 0))
        metric_cols[1].metric("Embeddings", result.get("embeddings_created", 0))
        metric_cols[2].metric("Inserted", result.get("inserted", 0))
        with st.expander("Storage result", expanded=True):
            st.json(result)

st.divider()
st.subheader("Ranked retrieval")
st.caption(
    "Questions run MongoDB vector search, reranking, evidence selection, and grounded "
    "LLM synthesis. Ranked chunks and source citations remain inspectable."
)
search_history = [
    message
    for message in st.session_state.get("messages", [])
    if message.get("role") == "assistant"
]
for index, message in enumerate(search_history):
    result_count = len(message.get("results", []))
    label = f"{message.get('query', 'Previous query')} | {result_count} ranked chunks"
    with st.expander(label, expanded=index == len(search_history) - 1):
        render_search_response(message)
        if message.get("results") and st.button(
            "Rerun reranking"
            if message.get("reranked_results") is not None
            else "Retry reranking",
            key=f"rerank-history-{index}",
            icon=":material/sort:",
        ):
            try:
                with st.spinner("Reranking every retrieved candidate..."):
                    rerank_search_message(api_url, message)
                message.pop("rerank_error", None)
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))

query = st.chat_input("Ask the smoke collection a question")
if query:
    payload = {
        "mongodb_db": database,
        "mongodb_collection": collection,
        "query": query,
        "top_k": int(top_k),
        "min_score": float(min_score),
        "num_candidates": None if exact else int(num_candidates),
        "exact": exact,
        "source_id_filter": source_id_filter,
        "title_filter": title_filter,
        "section_filter": section_filter,
        "chunk_id_filter": chunk_id_filter,
    }
    try:
        with st.spinner("Retrieving evidence, reranking, and synthesizing an answer..."):
            response = api_request("POST", api_url, "/api/ask", payload=payload, timeout=180)
        results = response.get("results", [])
        message = {
            "role": "assistant",
            "query": query,
            "content": f"Retrieved {len(results)} ranked source chunk(s) from `{database}.{collection}`.",
            "answer": response.get("answer"),
            "citations": response.get("citations", []),
            "insufficient_evidence": response.get("insufficient_evidence", False),
            "results": results,
            "reranked_results": results,
            "evidence": response.get("evidence", []),
            "response": response,
        }
        st.session_state.setdefault("messages", []).append(message)
        with st.expander(f"{query} | {len(results)} ranked chunks", expanded=True):
            render_search_response(message)
            if not results:
                st.info("No chunks met the selected threshold and filters.")
            elif st.button(
                "Rerun reranking"
                if message.get("reranked_results") is not None
                else "Retry reranking",
                key=f"rerank-new-{len(search_history)}",
                icon=":material/sort:",
            ):
                with st.spinner("Reranking every retrieved candidate..."):
                    rerank_search_message(api_url, message)
                message.pop("rerank_error", None)
                st.rerun()
    except ApiError as exc:
        st.error(str(exc))
