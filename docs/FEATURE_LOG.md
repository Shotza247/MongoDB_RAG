---
noteId: "d8868630b26211f190061541d53f6be1"
tags: []

---

# Feature Log

## 2026-11-01 - Local Portfolio Ask CORS

- Added configurable FastAPI CORS origins with localhost-only defaults for testing the
  portfolio's `/api/ask` call.
- Added preflight coverage for the approved local origin and an unapproved origin.
- Documented that deployed portfolio origins must be explicitly configured server-side.

## 2026-10-31 - API Review And Validation Coverage

- Added FastAPI route-contract and OpenAPI assertions for `POST /api/ask`.
- Corrected exception types for invalid structured-answer and evidence input.
- Verified the full test suite and Ruff checks before the initial project commits.

## 2026-10-26 - Chat Model Access Guard

- Replaced the inaccessible `gpt-5.4-mini` example with `gpt-5.5` for local setup.
- Updated the local `.env` chat model to `gpt-5.5` for Streamlit `/api/ask` testing.
- Added a provider-side guard that fails fast with an actionable configuration message
  if a known inaccessible OpenAI model is selected.

## 2026-10-25 - LangGraph OpenAI Grounded-Answer Workflow

- Orchestrated reranking, best-evidence selection, grounding prompt creation, chat
  generation, citation validation, and insufficient-evidence handling with LangGraph.
- Added environment-driven `CHAT_PROVIDER` and `CHAT_MODEL` selection; provider
  credentials remain server-side. The active local runtime had no `CHAT_MODEL` set
  during the 2026-10-25 live check, so successful generation was not yet verified.
- Documented future profile-agent tools for resume retrieval and opportunity intake.
  Outbound email requires validated inputs and explicit approval before sending.
- LiteLLM gateway/budget policies and Hugging Face routing remain a later phase.
- No live model call or test suite was run for this change.

## 2026-10-25 - Schema-Constrained Grounded Answers

- Added the Pydantic `GroundedAnswer` output contract and changed the LangGraph
  generation step to request provider-supported structured output.
- Kept strict application validation of inline evidence IDs and source/chunk
  resolution after structured parsing.
- Added focused workflow regression coverage for mapping and Pydantic responses.
- Verification so far: changed Python files parse successfully. The focused test
  and live retest are pending; approval to build an isolated verification image was
  denied, so the existing API container was left unchanged.

## 2026-09-27 - Direct Grounded LLM Answers

- Added `POST /api/ask` to retrieve from Atlas, rerank, select up to five evidence
  chunks, and synthesize with the configured LangChain chat provider adapter.
- Validated the answer structure and inline evidence IDs, then resolved citations to
  trusted source/chunk metadata and retrieval scores.
- No-result retrieval returns an insufficient-evidence answer without a model call.
- Streamlit now displays synthesized answers, citations, and ranked score details.
- LiteLLM budget routing and the hosted browser UI answer display remain future work.

## 2026-09-27 - Evidence Selection And Grounding Contract

- Added a provider-neutral selector for unique chunks ordered by `rerank_score`,
  returning at most five and reporting whether three were available.
- Preserved `source_id`, `chunk_id`, text, title, section, and retrieval scores.
- Added prompt construction that treats retrieved text as untrusted input and
  requires inline `[E1]` labels for factual claims.
- Defined and validated the JSON response contract: `answer`, `citation_ids`, and
  `insufficient_evidence`.
- Mapped accepted evidence labels to trusted source and chunk metadata.
- Actual model invocation, LiteLLM routing, LangGraph, and `/api/ask` remain future
  steps.

This file records user-facing capabilities and important architecture milestones in
delivery order. Detailed commands, failures, fixes, and verification evidence remain
in `docs/test-ui-audit.md`; the current implementation state is summarized in
`docs/project-status.md`.

## 2026-09-17 - Automatic Browser Search And Reranking

- Updated the FastAPI-hosted browser lab to call `/api/search` and then
  `/api/rerank` automatically for every submitted query.
- Displayed MongoDB `vector_score` and Voyage `rerank_score` side by side.
- Preserved title, text, `source_id`, and `chunk_id` through reranking.
- Retained the raw search and rerank responses for inspection.
- Added a browser UI contract test for the chained endpoint flow.
- Verified a live query returned and reranked three candidates.
- Increased the verified test baseline to 26 passing tests.

## 2026-09-16 - Domain-Oriented Project Architecture

- Reorganized runtime code into `api`, `core`, `ingestion`, `chunking`,
  `embeddings`, `vectorstore`, `retrieval`, and `llm` packages.
- Made `mongodb_vector_test_ui.api.fastapi:app` the explicit production, Docker,
  and Vercel launch target.
- Retained `mongodb_vector_test_ui.api.starlette:app` as the MVP1 fallback.
- Updated imports, scripts, tests, Docker, Compose, Vercel, and documentation.
- Removed generated test and lint caches from the project root.
- Documented why generic empty `utils`, `logs`, and `prompts` packages were omitted.
- Verified 25 tests, Ruff, FastAPI imports, live status, MongoDB connectivity, and a
  READY Atlas Vector Search index.

## 2026-09-16 - FastAPI Runtime And Vercel Foundation

- Added FastAPI as the required MVP2 API framework.
- Preserved all twelve MVP1 endpoint paths through the FastAPI application.
- Added OpenAPI metadata and interactive `/docs` support.
- Added the Vercel ASGI entry point at `api/index.py` and `vercel.json`.
- Added Docker and Compose workflows for machines where Windows Application
  Control blocks `pydantic_core`.
- Kept Starlette as a reference and fallback instead of treating it as the future
  production API.

## 2026-09-12 - Automatic Streamlit Reranking

- Changed Streamlit query submission to run MongoDB vector search and Voyage
  reranking automatically.
- Displayed vector and rerank scores together for every returned candidate.
- Added rerun and retry controls while keeping raw endpoint responses available.
- Reorganized API status, MongoDB target, and retrieval controls in the sidebar.
- Added collapsible ranked-source sections so earlier result groups remain usable.
- Added `docs/project-status.md` as the reconciled current-state handoff.

## 2026-09-12 - Voyage Reranker API

- Added a provider-neutral reranker adapter with Voyage `rerank-2.5` as the first
  implementation.
- Added `POST /api/rerank` for reranking existing candidates without losing source
  evidence or original vector scores.
- Returned all candidates during the evaluation phase with `rerank_score` and
  `rerank_position`.
- Added an identity fallback for provider-independent tests.
- Added an isolated live reranker smoke-test script.

## 2026-09-05 - Reusable Template Second-Collection Test

- Validated the reusable flow against
  `RAG_with_MongoDB.mvp1_template_smoke_chunks`.
- Confirmed document ingestion, Voyage embedding, index creation, retrieval, and
  source, title, and chunk-ID filtering in a second collection.
- Added an independent Streamlit HTTP client for testing reusable API behavior.

## 2026-09-05 - Atlas Vector Index Closeout

- Added `scripts/update_vector_index.py` to create or update the Atlas Vector
  Search index from the shared MVP1 definition.
- Updated the live `RAG_with_MongoDB.profile_chunks` index.
- Verified the index was READY, queryable, and included filter paths for source ID,
  title, section, and chunk ID.
- Verified filtered retrieval through the local API.

## 2026-09-05 - Retrieval Quality Controls

- Added `top_k`, minimum similarity score, `numCandidates`, exact nearest-neighbor
  mode, and source, title, section, and chunk-ID filters.
- Set the default minimum vector score to `0.6`.
- Allowed thresholding to return fewer than `top_k` results.
- Added clear compatibility errors when a selected filter is missing from the
  active vector index definition.
- Added retrieval pipeline, score threshold, exact mode, candidate count, and
  filter-composition tests.

## 2026-09-04 - MongoDB Database And Collection Browser

- Added controls for browsing databases and collections visible to the configured
  Atlas user.
- Added collection summaries for document count, regular indexes, search indexes,
  sample fields, titles, and source IDs.
- Allowed status, index creation, document storage, and vector search to target a
  selected database and collection without editing `.env`.
- Added safe database and collection name validation.

## 2026-09-01 - Mermaid Architecture Documentation

- Added GitHub-native Mermaid diagrams to the README and architecture documents.
- Documented ingestion, retrieval, reranking, API, and future LLM flows.

## 2026-09-01 - MVP1 Architecture And GitHub Planning

- Added MVP1 architecture and project-structure documentation.
- Added the MVP2 preview for reranking, grounded answers, citations, and chat APIs.
- Added GitHub-ready milestones, MVP1 and MVP2 issue backlogs, issue templates,
  project-board guidance, and CLI import notes.
- Added the reusable document-to-vector pipeline template.

## 2026-09-01 - Document Ingestion Pipeline UI

- Added drag-and-drop, file-picker, and local-path document extraction.
- Added TXT, Markdown, CSV, JSON, HTML, DOCX, and PDF support.
- Added extracted-text review before chunking and embedding.
- Added chunk preview and the `Chunk, Embed, and Store` workflow.
- Added document extraction tests and PDF extraction through `pypdf`.
- Verified a live document write, Voyage embedding, MongoDB storage, and retrieval.

## 2026-09-01 - Reusable Audit Trail

- Added a reusable audit approach for setup, errors, fixes, and verification.
- Added append-only audit tooling while keeping secrets and private content out of
  Markdown logs.
- Expanded `docs/test-ui-audit.md` as the project's detailed technical history.

## 2026-08-31 - Safe Environment Diagnostics

- Added `scripts/check_env.py` to validate MongoDB and embedding configuration
  without printing secrets.
- Replaced the misleading MongoDB placeholder hostname in `.env.example`.
- Added safe URI-shape, hostname, key-presence, model, and target diagnostics.
- Made the UI status endpoint report configuration issues clearly.

## 2026-08-31 - MongoDB Vector Search Lab Foundation

- Added the initial Starlette browser UI for MongoDB Vector Search experiments.
- Added direct Voyage and OpenAI REST embedding support.
- Added status, vector-index creation, document indexing, and search endpoints.
- Added local hashing embeddings for no-key plumbing tests.
- Added initial chunking and embedding tests.
- Created `docs/test-ui-audit.md` for reproducible setup and smoke-test notes.
## 2026-10-25 - Portfolio Chat Integration And Vercel Handoff

- Documented the FastAPI POST /api/ask contract for the portfolio client.
- Recorded that the route, Vercel entry point, and vercel.json exist while provider acceptance, preview deployment, CORS/abuse controls, and website integration remain pending.
- Added preview-to-production acceptance steps and the server/browser secret boundary.
- Required real LLM-provider acceptance, multi-chunk synthesis, and citation/no-context/error checks before website integration.
- No runtime implementation or deployment was performed by this documentation update.
