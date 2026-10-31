---
noteId: "74c65490b26211f190061541d53f6be1"
tags: []

---

# MongoDB RAG Lab

A reusable Retrieval-Augmented Generation foundation for extracting documents,
creating embeddings, storing vectors in MongoDB Atlas, retrieving relevant chunks,
and reranking them before grounded LLM answer generation.

The project began as the retrieval backbone for a portfolio Profile Agent. It is
structured as a general lab so the same ingestion, indexing, retrieval, evaluation,
and API workflow can be reproduced for other document collections and projects.

## Why This Project Exists

RAG systems are easier to trust when every stage can be inspected independently.
This repository therefore separates document extraction, chunking, embeddings,
vector storage, search, reranking, APIs, and test clients instead of hiding the
entire process behind one chat interface.

The retrieval test surfaces answer these questions independently, so search quality
can be inspected before generation:

- Was the document text extracted correctly?
- Which chunks and embeddings were stored?
- Is the MongoDB vector index ready and correctly configured?
- Which chunks passed the vector similarity threshold?
- How did semantic reranking change their order?
- Which `source_id` and `chunk_id` should support the final answer?

FastAPI exposes `POST /api/ask` for grounded answer generation. A LangGraph workflow
reranks candidates, selects evidence, builds the grounding prompt, invokes the
configured LangChain chat model through typed structured output, validates citations,
and returns an insufficient-evidence response without calling the model when retrieval
yields no evidence. The structured-output fix is applied, but focused tests and a
post-fix live provider acceptance are pending; website integration has not started.

## Current Capabilities

- Extract TXT, Markdown, CSV, JSON, HTML, DOCX, and PDF documents.
- Review extracted text before it is chunked or stored.
- Preview deterministic chunks grouped on paragraph boundaries.
- Create Voyage, OpenAI, or local hashing embeddings.
- Store and replace document chunks in MongoDB Atlas.
- Create, inspect, and update the Atlas Vector Search index.
- Browse accessible databases, collections, indexes, fields, and source metadata.
- Search with `top_k`, `numCandidates`, minimum score, exact mode, and metadata filters.
- Rerank MongoDB candidates with Voyage `rerank-2.5`.
- Display `vector_score` and `rerank_score` with source evidence.
- Use either the built-in browser lab or the independent Streamlit client.
- Expose the workflow through FastAPI with OpenAPI documentation.

Grounded answer generation and POST /api/ask are implemented in FastAPI, including
retrieval, reranking, evidence selection, and citation validation. Route and OpenAPI
coverage are tested; live chat-provider acceptance and deployment verification are
still pending. Website integration is pending.
LangGraph orchestrates the answer workflow. OpenAI is the selected MVP2 chat provider,
but the active local runtime had no `CHAT_MODEL` set during the latest check. An
isolated `gpt-5-mini` request was inaccessible; pre-fix `gpt-5.1` failed JSON parsing.
See `docs/project-status.md` for the current handoff and
`templates/document-vector-pipeline/PIPELINE_AUDIT.md` for chronological evidence.
Voyage remains responsible for embeddings and reranking.

The Vercel entry point and vercel.json already exist. The API is prepared but not
deployed; see docs/fastapi-vercel-setup.md and
docs/portfolio-chat-integration.md for deployment and acceptance steps.

## Retrieval Flow

```mermaid
flowchart LR
    document["TXT / DOCX / PDF / CSV / JSON / HTML"] --> extract["Extract and review text"]
    extract --> chunk["Create stable chunks"]
    chunk --> embedDoc["Create document embeddings"]
    embedDoc --> store["MongoDB Atlas Vector Store"]

    question["User question"] --> embedQuery["Voyage query embedding"]
    embedQuery --> search["MongoDB Atlas Vector Search"]
    store --> search
    search --> candidates["Candidate chunks + vector_score"]
    candidates --> rerank["Voyage rerank-2.5"]
    rerank --> ranked["Ranked chunks + rerank_score"]
    ranked --> graph["LangGraph answer workflow"]
    graph --> select["Retain best 3-5 evidence chunks"]
    select --> prompt["Grounding prompt"]
    prompt --> chat["OpenAI chat model"]
    chat --> validate["Validate evidence citations"]
    validate --> answer["Grounded answer + verified citations"]
```

MongoDB produces `vector_score` from vector similarity. Voyage produces
`rerank_score` by evaluating the question directly against each candidate's text.
Both UIs automatically call `/api/search` and then `/api/rerank` while preserving
the original source metadata.

## Architecture

FastAPI is the primary local, Docker, and Vercel application. Starlette is retained
as the verified MVP1 fallback while its handler logic is incrementally converted to
native typed FastAPI contracts.

```text
src/mongodb_vector_test_ui/
  api/
    fastapi.py             # Primary API application
    starlette.py           # Verified MVP1 handlers and browser UI
  core/config.py           # Environment loading and safe diagnostics
  ingestion/documents.py   # Document extraction
  chunking/service.py      # Chunk creation
  embeddings/providers.py  # Embedding adapters
  vectorstore/mongodb.py   # Atlas storage, index, and vector search
  retrieval/rerankers.py   # Reranker adapters
  llm/providers.py         # LangChain-compatible chat-model adapters
```

See [Project Structure](docs/architecture/project-structure.md) for the complete
repository map and architectural ownership rules.

## Prerequisites

- Python 3.11 or newer; Python 3.12 is recommended.
- A MongoDB Atlas cluster and database user.
- A MongoDB Atlas Vector Search-capable cluster.
- A Voyage/Atlas Model API key for the configured embedding and reranking flow.
- Docker Desktop if Windows Application Control blocks local Python dependencies.

## Local Setup

Clone the repository and create a fresh virtual environment:

```powershell
git clone <your-repository-url>
cd MongoDB_RAG
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,orchestration,openai]"
```

For a runtime-only installation:

```powershell
python -m pip install -r requirements.txt
```

`pyproject.toml` is the authoritative package definition. `requirements.txt`
mirrors its core runtime dependencies for conventional installation workflows.

## Configure The Environment

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

At minimum, replace these placeholders:

```text
MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/
MONGODB_DB=RAG_with_MongoDB
MONGODB_COLLECTION=profile_chunks
VOYAGE_API_KEY=your-key
OPENAI_API_KEY=your-key
CHAT_PROVIDER=openai
CHAT_MODEL=gpt-5.5
```

`OPENAI_API_KEY` is used for answer generation; Voyage remains the embedding and
reranking provider. The model call is made only when `POST /api/ask` has evidence to
ground an answer. Keep keys in `.env` locally and in server-side environment
settings when deployed. Do not use `gpt-5.4-mini`; this project has already returned
`model_not_found` for that model. Use an enabled chat model such as `gpt-5.5`,
`gpt-5.1`, or `o4-mini`, then restart FastAPI before testing from Streamlit.
Confirm model access for the actual deployment project before relying on it.

Never commit `.env`. Validate the configuration without printing secrets:

```powershell
python scripts\check_env.py
```

## Prepare MongoDB Atlas

Create or reconcile the selected collection's vector index:

```powershell
python scripts\update_vector_index.py `
  --database RAG_with_MongoDB `
  --collection profile_chunks `
  --wait
```

The index expects a 1024-dimensional cosine vector field named `embedding` and
supports filters for source ID, title, section, and chunk ID. Adjust the matching
environment variables when using another embedding model or schema.

## Run FastAPI

```powershell
python -m uvicorn mongodb_vector_test_ui.api.fastapi:app `
  --host 127.0.0.1 `
  --port 8765 `
  --http h11
```

Open:

- Browser retrieval lab: `http://127.0.0.1:8765/`
- Interactive API documentation: `http://127.0.0.1:8765/docs`
- OpenAPI schema: `http://127.0.0.1:8765/openapi.json`

Use the browser lab to inspect MongoDB, upload a document, preview chunks, embed and
store it, then run vector search and Voyage reranking.

## Run The Streamlit Client

The reusable Streamlit UI is an independent HTTP client and can test the local or a
hosted API without importing service internals.

```powershell
python -m pip install -r templates\document-vector-pipeline\requirements-streamlit.txt
python -m streamlit run templates\document-vector-pipeline\streamlit_app.py `
  --server.port 8501
```

Set its API URL to `http://127.0.0.1:8765` and select the database and collection
from the sidebar.

## Run With Docker

Use Docker when the Windows Python environment is unavailable or
`pydantic_core` is blocked by Application Control:

```powershell
docker compose up --build
```

This starts FastAPI on port `8765` and Streamlit on port `8501`. Credentials are
read from the ignored local `.env` file and are not copied into the image.

## Verify The Installation

```powershell
python -m pytest -q
python -m ruff check src tests scripts api
python scripts\test_reranker.py
```

The latest local test run passed all 30 tests. Live FastAPI, MongoDB, vector-index,
retrieval, reranking, and chat-provider acceptance must be checked separately; see
[Project Status](docs/project-status.md) for current evidence and remaining work.

## Reuse For Another Project

1. Copy the repository or `templates/document-vector-pipeline/`.
2. Create a new `.env` from `.env.example`.
3. Select a dedicated MongoDB database and collection.
4. Confirm embedding dimensions and update the Atlas index definition if required.
5. Ingest a representative document and inspect the extracted text.
6. Preview chunks before storing them.
7. Run retrieval with a known-answer question.
8. Compare vector and rerank scores while checking source IDs and chunk IDs.
9. Record the smoke test and configuration decisions in the project audit.
10. Add LLM synthesis only after retrieval quality is acceptable.

This sequence keeps retrieval problems separate from prompt and model problems.

## API Summary

| Purpose | Endpoint |
| --- | --- |
| Health and safe diagnostics | `GET /api/status` |
| Browse MongoDB targets | `GET /api/mongodb/databases`, `GET /api/mongodb/collections` |
| Inspect a collection | `GET /api/mongodb/collection/summary` |
| Create or inspect the vector index | `POST /api/index/create` |
| Extract an uploaded or local document | `POST /api/document/extract/upload`, `POST /api/document/extract/path` |
| Preview chunks | `POST /api/document/chunks` |
| Chunk, embed, and store | `POST /api/index/document` |
| Retrieve vector candidates | `POST /api/search` |
| Rerank candidates | `POST /api/rerank` |
| Generate grounded answer with verified citations | `POST /api/ask` |

See [API Reference](docs/api-reference.md) for payloads, responses, and examples.

## Documentation

- [Feature Log](docs/FEATURE_LOG.md): chronological record of delivered capabilities.
- [Project Status](docs/project-status.md): current verified state and MVP2 handoff.
- [MVP1 Architecture](docs/architecture/mvp1-architecture.md): retrieval foundation.
- [MVP2 Preview](docs/architecture/mvp2-preview.md): LangGraph answer flow, model adapter, and planned profile-agent tools.
- [Project Structure](docs/architecture/project-structure.md): source ownership and layout.
- [FastAPI And Vercel Setup](docs/fastapi-vercel-setup.md): deployment preparation.
- [Test UI Audit](docs/test-ui-audit.md): detailed debugging and verification trail.

## Roadmap

1. Replace delegated Starlette parsing with typed FastAPI request/response models.
2. Complete live OpenAI `/api/ask` acceptance, including answer quality and citation checks.
3. Add resume retrieval and opportunity-intake tools to the LangGraph agent; request
   a missing recipient email and validate job-posting URLs.
4. Select a resume source and email provider. Require explicit approval before every
   outbound email.
5. Add approved Google Drive document synchronization if needed for corpus freshness.
6. Deploy and verify the FastAPI endpoints on Vercel.
7. Integrate the hosted service into the portfolio Profile Agent; add LiteLLM routing
   and budgets later for Hugging Face or other provider routes.

## Security And Publishing

Do not commit `.env`, API keys, MongoDB credentials, private source documents,
virtual environments, caches, or local logs. `.gitignore` already excludes these
paths, but review staged files before every commit:

```powershell
git status
git diff --cached
```
