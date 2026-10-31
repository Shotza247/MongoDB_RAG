---
noteId: "eeacd930b1dd11f190061541d53f6be1"
tags: []

---

# Project Structure

The repository is organized by RAG responsibility. FastAPI is the production API;
Starlette is retained in the same API package as the verified MVP1 fallback. Domain
modules do not import either web framework, so they can be reused by APIs, scripts,
tests, and future workers.

## Architecture Map

```mermaid
flowchart LR
    clients["Browser / Streamlit / Portfolio"] --> fastapi["api/fastapi.py<br/>Primary ASGI API"]
    fastapi --> fallback["api/starlette.py<br/>Verified MVP1 handlers"]
    fallback --> ingest["ingestion/documents.py"]
    fallback --> chunks["chunking/service.py"]
    fallback --> embed["embeddings/providers.py"]
    fallback --> store["vectorstore/mongodb.py"]
    fallback --> rank["retrieval/rerankers.py"]
    fallback --> models["llm/providers.py"]
    ingest --> chunks --> embed --> store
    store --> rank
    config["core/config.py"] --> fastapi
    config --> fallback
    config --> embed
    config --> store
    config --> rank
    config --> models

    classDef api fill:#eaf2ff,stroke:#2563eb,color:#0f1f3d;
    classDef domain fill:#e8f5ef,stroke:#1f8f5f,color:#0d2f22;
    classDef core fill:#fff4d6,stroke:#b7791f,color:#3d2905;
    class fastapi,fallback api;
    class ingest,chunks,embed,store,rank,models domain;
    class config core;
```

## Repository Map

```text
MongoDB_RAG/
  api/
    index.py                       # Vercel ASGI entry point
  docs/
    architecture/                  # Current architecture and MVP boundaries
    github/                        # Milestones, issues, and project-board plans
    api-reference.md
    FEATURE_LOG.md                   # Chronological capability history
    fastapi-vercel-setup.md
    project-status.md              # Current-state handoff
    test-ui-audit.md               # Chronological implementation record
  scripts/
    check_env.py
    test_reranker.py
    update_vector_index.py
  src/mongodb_vector_test_ui/
    api/
      fastapi.py                   # Primary FastAPI application
      starlette.py                 # MVP1 fallback and verified handlers
    core/
      config.py                    # Environment and safe diagnostics
    ingestion/
      documents.py                 # TXT, MD, CSV, JSON, HTML, DOCX, PDF extraction
    chunking/
      service.py                   # Deterministic paragraph-grouped chunks
    embeddings/
      providers.py                 # Voyage, OpenAI, and local hashing adapters
    vectorstore/
      mongodb.py                   # Atlas index, storage, browsing, vector search
    retrieval/
      rerankers.py                 # Provider-neutral reranking and Voyage adapter
    llm/
      providers.py                 # LangChain-compatible chat provider factory
  templates/document-vector-pipeline/
    streamlit_app.py               # Reusable HTTP evaluation client
    docs/
    scripts/
  tests/                            # Unit and API contract tests
  .env.example
  .gitignore
  compose.yaml
  Dockerfile
  pyproject.toml
  README.md
  vercel.json
```

## API Ownership

- Run `mongodb_vector_test_ui.api.fastapi:app` for local development, Docker, and
  production deployment.
- `api/index.py` exports that same FastAPI app for Vercel.
- Run `mongodb_vector_test_ui.api.starlette:app` only for fallback comparison or
  MVP1 regression checks.
- The current FastAPI route table delegates to the verified Starlette handlers.
  Typed FastAPI request/response models can replace those handlers incrementally
  without changing the public endpoint contract.

## Deliberately Omitted

- No generic `utils/` package: helpers remain with the domain that owns them.
- No committed `logs/` directory: runtime logs belong in stdout or the hosting
  platform, not source control.
- No empty `prompts/` package: grounded-answer prompts will be added with `/api/ask`.
- No root `main.py`: the explicit ASGI paths avoid a second ambiguous entry point.
- The reference GIF is not copied into the repository because it is design input,
  not a runtime or documentation dependency.

## Publishing Hygiene

Do not commit `.env`, `.venv/`, `.uv-cache/`, Python caches, test caches, generated
package metadata, private documents, or local logs. Keep `.env.example`, tests,
architecture decisions, and reproducible operational scripts under version control.

Historical paths in `docs/test-ui-audit.md` are intentionally preserved because
that file records what existed when each event occurred. Current paths are defined
by this document and `docs/project-status.md`.
