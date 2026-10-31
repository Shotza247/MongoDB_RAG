# MVP2 GitHub Issues

These are planning issues for the next phase after MVP1 is committed.

## Issue 0 - Port The Verified API Contract To FastAPI

Labels: `feature`, `api`, `fastapi`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

### Description

Make FastAPI the project API layer, preserve the existing route paths and evidence
fields, and prove that the browser and Streamlit UIs work before LLM integration.

### Acceptance Criteria

- FastAPI and Pydantic pass the local dependency import gate.
- Existing status, browsing, ingestion, search, and rerank routes are ported.
- Request and response models produce OpenAPI documentation.
- Existing browser and Streamlit UI acceptance tests pass against FastAPI.
- Vercel discovers the exported FastAPI `app` entry point.
- Starlette is removed as a direct project dependency after parity is verified.

## Issue 1 - Add Reranking Layer After MongoDB Retrieval

Labels: `feature`, `reranking`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

Implementation status: adapter, `/api/rerank`, MongoDB candidate handoff, and
automatic Streamlit score comparison are complete and live-tested. Best-3-5 selection and
integration into `/api/ask` remain open.

### Description

Retrieve a larger candidate set from MongoDB Vector Search, then rerank the candidates before sending evidence to the LLM.

### Acceptance Criteria

- Reranker interface exists.
- Voyage rerank is supported first.
- Reranking can be toggled on/off.
- Response includes original vector score and rerank score.
- Tests cover reranked ordering and fallback behavior.

## Issue 2 - Add Grounded Answer Generation Endpoint

Labels: `feature`, `llm`, `api`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

### Description

Add an endpoint that retrieves evidence chunks, selects the best 3-5 chunks, and asks an LLM to produce a concise grounded answer.

### Acceptance Criteria

- `/api/ask` or `/api/chat` endpoint exists.
- Endpoint accepts a user question and top-k settings.
- LLM receives only selected evidence chunks.
- Response includes answer text and citations.
- No-context behavior is handled gracefully.

## Issue 3 - Add Citation Mapping

Labels: `feature`, `citations`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

### Description

Ensure generated answers cite source chunks returned from retrieval/reranking.

### Acceptance Criteria

- Each citation includes `source_id`, `chunk_id`, `title`, and score fields.
- UI shows cited chunks below the answer.
- Prompt instructs the LLM not to cite unavailable evidence.
- Tests cover citation mapping.

## Issue 4 - Add LLM Provider Configuration

Labels: `configuration`, `llm`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

### Description

Add environment configuration for the LLM provider used for answer generation.

### Acceptance Criteria

- `.env.example` includes non-secret LLM settings.
- OpenAI is the default answer-generation provider.
- Missing key diagnostics are safe and clear.
- README explains provider choices.

## Issue 5 - Add Answer UI

Labels: `frontend`, `llm`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

### Description

Extend the test UI so users can ask a question and view a concise answer, cited chunks, and retrieval diagnostics.

### Acceptance Criteria

- UI has a clear ask/chat panel.
- Answer text is visible and concise.
- Citations are shown with source metadata.
- Raw retrieval/reranking diagnostics remain available.

## Issue 6 - Add Answer Quality Smoke Tests

Labels: `testing`, `evaluation`, `mvp2`
Milestone: `MVP2 - FastAPI And Grounded LLM Answers`

### Description

Add small repeatable tests for prompt construction, no-context behavior, citation shape, and API response structure.

### Acceptance Criteria

- Unit tests cover prompt assembly.
- API smoke command exists for `/api/ask`.
- Audit log records at least one answer-generation smoke test.
- README explains how to run the smoke test.
