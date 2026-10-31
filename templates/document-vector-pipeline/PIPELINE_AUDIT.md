# Pipeline Audit

Use this file as the running setup/debug log for each document-to-vector project.

## YYYY-MM-DD HH:mm - New Project Baseline

- Status: investigating | fixed | passed | blocked
- Goal: documents should be extracted, reviewed, chunked, embedded, stored in MongoDB, and queried through a test UI/API.
- Environment:
  - Python:
  - OS:
  - MongoDB target:
  - Embedding provider:
  - Test UI/API host:
- Commands:
  - `python --version`
  - `python -m pip install -e ".[dev]"`
  - `python scripts\check_env.py`
  - `python scripts\update_vector_index.py --database <db> --collection <collection> --wait`
  - `python -m uvicorn <package>.app:app --host 127.0.0.1 --port 8765 --http h11`
- Evidence:
  - Documents extracted:
  - Extracted characters:
  - Chunks created:
  - Embeddings created:
  - MongoDB collection:
  - Vector index:
  - Vector index status:
  - Vector index filter paths:
  - Visible databases:
  - Selected collection:
  - `/api/status` result:
  - `/api/mongodb/databases` result:
  - `/api/mongodb/collection/summary` result:
  - `/api/document/chunks` result:
  - `/api/index/document` result:
  - `/api/search` result:
  - Retrieval controls:
  - Source ID filter result:
  - Title filter result:
  - Section filter result:
  - Chunk ID filter result:
- Issues:
  - None yet.
- Changes:
  - None yet.
- Follow-up:
  - None yet.

## 2026-08-29 - Reference Baseline From Profile Agent RAG

- Status: passed
- Goal: Ingest a master career profile into MongoDB Atlas Vector Search using Voyage embeddings.
- Environment:
  - Python: 3.12.10
  - OS: Windows
  - MongoDB target: `RAG_with_MongoDB.profile_chunks`
  - Embedding provider: Voyage through `https://ai.mongodb.com/v1`
  - API host: `127.0.0.1:8765`
- Evidence:
  - Documents loaded: 1
  - Chunks created: 117
  - Embeddings created: 117
  - Vector index: `profile_vector_index`
  - Framework decision: Starlette was used to avoid the blocked `pydantic_core` dependency in the local MVP path.
  - `/health`: returned `mongo_ok: True`
  - `/ask`: returned source-backed chunks
- Issues:
  - Windows Application Control blocked Pydantic native DLLs.
  - Direct Voyage endpoint returned 403 when used with a MongoDB Atlas Model API key.
- Changes:
  - Used stdlib config instead of `pydantic-settings`.
  - Used Starlette instead of FastAPI for MVP runtime.
  - Used direct REST calls instead of Voyage/OpenAI Python SDKs.
  - Set `VOYAGE_BASE_URL=https://ai.mongodb.com/v1`.
- Follow-up:
  - Apply the same checks to hosted API deployment.

## 2026-09-05 - Reference Reusable Template Second Collection Test

- Status: passed
- Goal: Prove the MVP1 template can be reused against a second MongoDB collection without changing the core app code.
- Environment:
  - Python: 3.12.10
  - OS: Windows
  - MongoDB target: `RAG_with_MongoDB.mvp1_template_smoke_chunks`
  - Embedding provider: Voyage through `https://ai.mongodb.com/v1`
  - Test UI/API host: `127.0.0.1:8767`
- Evidence:
  - Starting collection state: reachable, empty, and no search indexes.
  - Source ID: `mvp1-template-smoke-test`
  - Title: `MVP1 Reusable Template Smoke Test`
  - Chunks created: 1
  - Embeddings created: 1
  - Chunks inserted: 1
  - Vector index: `profile_vector_index`
  - Vector index status: `READY`, queryable
  - Vector index filter paths: `metadata.source_id`, `metadata.title`, `metadata.section`, `chunk_id`
  - Plain search result: returned expected chunk with score about `0.7569`
  - Source ID plus title filter result: returned expected chunk with score about `0.7363`
  - Chunk ID filter result: returned expected chunk with score about `0.6935`
- Decision:
  - Starlette remains acceptable for MVP1 reusable-template validation.
  - FastAPI remains the target candidate for the later hosted reusable API.
- Follow-up:
  - Use this entry as the expected validation shape when copying the template into another RAG project.

## YYYY-MM-DD HH:mm - MVP1 Document Ingestion UI Baseline

- Status: investigating | fixed | passed | blocked
- Goal: verify document extraction, chunk preview, MongoDB vector storage, and vector search retrieval through the MVP1 test UI.
- Environment:
  - Python:
  - OS:
  - MongoDB target:
  - Embedding provider:
  - Test UI/API host:
- Evidence:
  - Upload extraction:
  - File-path extraction:
  - Visible databases:
  - Selected database:
  - Selected collection:
  - Collection summary:
  - Extracted characters:
  - Chunk preview count:
  - Embeddings created:
  - Chunks inserted:
  - Vector index status:
  - Vector index filter paths:
  - Vector search result count:
  - Top source ID:
  - Minimum score:
  - numCandidates:
  - Exact mode:
  - Filter compatibility:
  - Source ID filter result:
  - Title filter result:
  - Section filter result:
  - Chunk ID filter result:
- Verification:
  - `python -m pytest`:
  - `python -m ruff check .`:
  - Live API smoke:
- Issues:
  - None yet.
- Follow-up:
  - Add reranker and grounded LLM answer endpoint in MVP2.

## 2026-09-07 - Independent Streamlit Reusability Client

- Status: partially verified
- Goal: validate that a second UI can browse targets and query ranked chunks using only the reusable Starlette HTTP contract.
- Scope: `streamlit_app.py`, `requirements-streamlit.txt`, `.env.example`, template README, and API reference.
- Changes:
  - Added API, database, collection, ranking, exact-search, and indexed-filter controls.
  - Added a chat-style query control that calls `POST /api/search` and displays ranked chunks with source references.
  - Set the reusable smoke collection and source ID as overridable defaults.
- Verification:
  - Bundled Python `py_compile`: passed for `streamlit_app.py`.
  - Live API probe: blocked because no service was listening at `127.0.0.1:8767`.
  - Rendered Streamlit check: pending because Streamlit and Requests are not installed in the available runtime, and the project virtual environment points to a removed Python installation.
- Follow-up:
  - Repair the virtual environment, install `requirements-streamlit.txt`, start Starlette on port `8767`, and run Streamlit on port `8501`.
  - Confirm the smoke query returns `mvp1-template-smoke-test` with score and chunk ID visible.

## 2026-09-07 - Streamlit Could Not Reach Starlette

- Status: partially fixed
- Symptom: `WinError 10061` while requesting `/api/status` at `127.0.0.1:8767`.
- Scope: independent Streamlit client to Starlette API connection.
- Suspected cause: confirmed that no process is listening on ports `8767` or `8765`.
- Evidence:
  - The Streamlit error is a TCP connection refusal, occurring before MongoDB or Voyage is called.
  - `.venv\pyvenv.cfg` points to a removed Python 3.12 installation, so its existing Python and Uvicorn launchers cannot create a working process.
- Changes:
  - No application-code change was required; the API client is addressing the configured URL correctly.
- Verification:
  - Port listener checks returned no Starlette process.
- Follow-up:
  - Recreate the virtual environment, install the project, and start Uvicorn on the same port configured in the Streamlit sidebar.

## 2026-09-07 - Streamlit Document Ingestion Workflow

- Status: implemented, live acceptance pending
- Goal: let a user validate the reusable pipeline with their own supported document through the independent Streamlit client.
- Scope: `streamlit_app.py`, template README, API reference, and smoke collection workflow.
- Changes:
  - Added drag/drop upload and server-side file-path extraction.
  - Added editable title, source ID, and extracted document text review.
  - Added chunk preview with chunk text, IDs, character counts, metadata, and raw response evidence.
  - Added an explicit chunk, embed, and store action targeting the selected MongoDB database and collection.
  - Added ingestion result metrics and a five-minute write timeout for larger embedding jobs.
  - Left the source filter empty by default so newly ingested documents are not hidden by the original smoke source filter.
- Verification:
  - Bundled Python `py_compile`: passed for the updated `streamlit_app.py`.
  - Source line-length check: passed with no lines over the project's 100-character Ruff limit.
  - Project Ruff and rendered UI checks remain pending because the existing `.venv` still points to a removed Python installation.
  - Live acceptance should use `RAG_with_MongoDB.mvp1_template_smoke_chunks` and a unique source ID.
- Follow-up:
  - Upload a small TXT or DOCX, preview its chunks, store it, then retrieve it through the chat using its source ID filter.

## 2026-09-07 - MongoDB Lab Layout And Collapsible Retrieval

- Status: partially verified
- Goal: reduce retrieval-result clutter and make the template's MongoDB-specific boundary explicit.
- Scope: Streamlit page identity, sidebar diagnostics, main-page inspection, and query history.
- Changes:
  - Renamed the page to `Reusable MongoDB RAG Retrieval Lab`.
  - Moved MongoDB connection status and the active database/collection target into the retrieval sidebar.
  - Kept detailed status JSON and collection inspection on the main page.
  - Grouped each query and its ranked source chunks into a collapsible result section.
  - Configured older result groups to collapse while the newest group remains expanded.
  - Corrected the five-minute timeout so it applies to chunk/embed/store rather than chunk preview.
- Verification:
  - Bundled Python `py_compile`: passed for the updated Streamlit client.
  - Source line-length check: passed with no lines over the project's 100-character Ruff limit.
  - Rendered interaction check remains pending because ports `8501` and `8767` were not listening in the accessible session.
- Follow-up:
  - Run two consecutive queries and confirm only the newest result group opens by default.

## 2026-09-07 - Atlas SRV Lookup Failure In Running API

- Status: partially fixed
- Symptom: Starlette returned HTTP 500 with `All nameservers failed` for the Atlas `_mongodb._tcp` SRV lookup.
- Scope: running Starlette process to MongoDB Atlas connection; Streamlit only surfaced the backend error.
- Evidence:
  - Safe environment diagnostics passed and identified the non-placeholder Atlas hostname.
  - Windows resolved the SRV record to three Atlas shard hosts.
  - Windows resolved the Atlas TXT record with the expected auth source and replica-set options.
  - The live `/api/status` endpoint continued returning the DNS error after the Windows DNS cache was flushed.
- Decision:
  - MongoDB URI configuration is not the current fault; the failure is isolated to DNS state or DNS access in the running Python/Uvicorn process.
- Changes:
  - Flushed the Windows DNS resolver cache; no application code or secrets changed.
- Verification:
  - Public/system DNS resolution passed.
  - Live Starlette MongoDB status still failed, indicating the process needs restarting or its runtime/network resolver needs repair.
- Follow-up:
  - Restart Starlette, then call `/api/status` again before restarting Streamlit.
  - If it persists, test the exact Python runtime's `dnspython` resolver and network/VPN DNS configuration.

## 2026-09-08 - Reusable LangChain And LangGraph Model Adapter

- Status: partially verified
- Goal: allow the grounded-answer graph to switch chat providers without changing graph or retrieval code.
- Scope: provider adapter, safe status diagnostics, optional dependencies, environment template, tests, and MVP2 architecture.
- Changes:
  - Added a common LangChain chat-model factory for OpenAI, Anthropic, xAI/Grok, and DeepSeek.
  - Exposed the same model interface for LangGraph nodes.
  - Kept Voyage wired as the current embedding provider and explicitly rejected it as a generative chat provider.
  - Added provider-specific optional dependency groups and secret-safe environment fields.
- Verification:
  - Python compilation passed for the adapter, Starlette integration, and provider tests.
  - `pyproject.toml` parsed successfully after adding optional dependency groups.
  - Provider-independent runtime checks passed for Grok-to-xAI aliasing, additional-provider pass-through, and Voyage embedding-role preservation.
  - Full pytest and real LangChain initialization remain pending because the project virtual environment still points to a removed Python installation and provider extras are not installed.
  - No external model request was made.
- Follow-up:
  - Select the first generative provider/model, install its optional dependency, and run one minimal invocation before building the grounded-answer graph.

## 2026-09-09 - Voyage Reranker Adapter

- Status: passed
- Goal: add and independently verify a reusable reranker before connecting reranking to MongoDB retrieval.
- Scope: reranker protocol, Voyage implementation, identity fallback, safe diagnostics, environment configuration, tests, and live smoke script.
- Changes:
  - Added provider-neutral candidate input and metadata-preserving reranked output.
  - Added Atlas Model API `/rerank` support using the existing model API key and base URL.
  - Added `vector_score`, `rerank_score`, and `rerank_position` evidence fields.
  - Added `RERANK_PROVIDER`, `VOYAGE_RERANK_MODEL`, and `RERANK_TIMEOUT_SECONDS`.
- Verification:
  - Focused pytest: 11 passed.
  - Focused Ruff: all checks passed.
  - Live synthetic rerank: passed using `rerank-2.5` through `https://ai.mongodb.com/v1/rerank`.
  - Corrected live response with explicit `top_k: null` returned all candidates.
  - Storage chunk ranked first at `0.7891`; retrieval chunk ranked second at `0.4102`; unrelated chunk moved from original vector score `0.83` to third at rerank score `0.2021`.
- Follow-up:
  - Connect MongoDB candidate results to this adapter, then retain the best 3-5 reranked chunks as the next isolated MVP2 task.

## 2026-09-10 - Reranker API And Streamlit Comparison

- Status: passed; manual UI acceptance completed on 2026-09-12.
- Goal: verify reranking through the reusable HTTP boundary before selecting context or generating an LLM answer.
- Scope: Starlette rerank route, independent Streamlit action, score comparison, metadata preservation, documentation, and regression coverage.
- Changes:
  - Added `POST /api/rerank` with question and candidate-list validation.
  - Forced `top_k=None` so this test returns all candidates in reranked order.
  - Added **Rerank retrieved chunks** to every Streamlit search result group.
  - Displayed original `vector_score` beside `rerank_score` and retained all candidate evidence fields.
  - Kept best-3-5 selection and grounded answer generation outside this change.
- Verification:
  - Python compilation passed for the Starlette app, Streamlit client, and reranker.
  - Focused Ruff passed with no findings.
  - Focused reranker and model-provider pytest suite: 11 passed.
  - Static route/UI wiring check confirmed `/api/rerank`, both score fields, return-all evidence, and both Streamlit rerank actions.
  - Live HTTP/UI acceptance later passed after Starlette and Streamlit were restarted.
- Next step:
  - Manually compare score/order changes in the Streamlit smoke collection, then implement best-3-5 selection as its own tested unit.

## 2026-09-12 - Streamlit API Status Priority

- Status: passed.
- Goal: show API and MongoDB availability before ingestion or retrieval actions.
- Changes:
  - Moved the API status result from the sidebar to the top of the main page.
  - Included the active database and collection in the successful status banner.
  - Kept the raw response directly below the banner and retrieval target in the sidebar.
- Verification:
  - Python compilation passed.
  - Ruff passed with no findings.
- Superseded layout note:
  - The following sidebar-order change moved the visible status back beneath the Starlette API URL, matching the final requested layout.

## 2026-09-12 - Streamlit Sidebar Control Order

- Status: passed.
- Goal: group connection and MongoDB target controls according to their dependencies.
- Changes:
  - Positioned API status directly below the Starlette API URL in the sidebar.
  - Placed the database load action beneath the database selector.
  - Placed the collection load action beneath the collection selector.
  - Positioned the active retrieval target beneath both target selectors.
  - Kept retrieval tuning controls and indexed filters in a separate lower section.
- Verification:
  - Python compilation passed.
  - Ruff passed with no findings.

## 2026-09-12 - Live Rerank UI Acceptance And Documentation Reconciliation

- Status: passed.
- Goal: prove both scores render and reconcile implementation status before LLM work.
- Evidence:
  - `/api/status`: HTTP 200; MongoDB connected; index READY; Voyage reranker configured as `rerank-2.5`.
  - Live `profile_chunks` search returned three candidates above `0.6`.
  - Live `/api/rerank` returned all three candidates with vector and rerank scores.
  - Streamlit rendered `Vector 0.665` and `Rerank 0.445` for the reusable smoke collection after the manual rerank action.
- Changes:
  - Added clear pre-rerank UI guidance explaining `Not run` and the required button action.
  - Added `docs/project-status.md` and reconciled README, architecture, API, milestone, issue, and template statements.
- Verification:
  - Full pytest suite: 22 passed.
  - Full Ruff check: passed.
  - Python compilation passed for the Starlette app, reranker, and Streamlit client.
  - All 12 implemented Starlette routes matched the root API reference.
- Follow-up:
  - Implement and test best-3-5 evidence selection before connecting OpenAI answer generation.

## 2026-09-12 - Automatic Search And Rerank Workflow

- Status: passed.
- Goal: show vector and rerank scores from one query submission.
- Design note:
  - Vector search and reranking are sequential, not parallel, because the reranker consumes the retrieved candidates.
- Changes:
  - Streamlit now calls `/api/rerank` automatically after a successful `/api/search`.
  - Successful results render both scores on first display.
  - Failed reranking preserves vector results, shows the provider error, and offers **Retry reranking**.
  - Successful result groups retain **Rerun reranking** for comparison testing.
  - Reconciled all current-facing README, API, architecture, status, milestone, and issue documentation.
- Follow-up:
  - Implement best-3-5 evidence selection before grounded answer generation.
- Verification:
  - Full pytest suite: 22 passed.
  - Ruff and Python compilation: passed.
  - Fresh Streamlit query rendered `Vector 0.732` and `Rerank 0.715` without a second action.
  - Raw `/api/search` and `/api/rerank` responses remained inspectable.

## 2026-09-12 - Starlette Backbone Documentation And Mermaid Flows

- Status: passed.
- Goal: document the working capabilities backbone before LLM synthesis work.
- Changes:
  - Declared Streamlit plus Starlette as the current retrieval, reranking, and LLM integration backbone.
  - Reframed FastAPI as optional at that time. Superseded on 2026-09-13 when FastAPI
    was confirmed as the required architecture and Vercel deployment target.
  - Updated the root architecture flow to include automatic MongoDB retrieval and Voyage reranking.
  - Added current-state and reusable-template request sequence diagrams.
  - Converted remaining plain-text pipeline descriptions to Mermaid flowcharts.
- Verification:
  - All 13 Mermaid blocks start with either `flowchart` or `sequenceDiagram`.
  - Line-based Markdown code-fence inspection found the reusable template fences balanced.
  - Current-facing FastAPI requirement/preference wording was removed.
- Follow-up:
  - Extend the MVP2 sequence after best-3-5 selection and `/api/ask` are implemented.

## 2026-09-13 - Project Cleanup And Required FastAPI Handoff

- Status: completed.
- Goal: retain useful runtime, test, documentation, reusable-template, and GitHub
  planning assets before the required FastAPI and grounded-answer phase.
- Removed:
  - Notebook/editor temporary files, lint/test caches, Python bytecode caches, package
    metadata, and unused virtual-environment content.
  - The old `.venv` after stopping only the project Uvicorn and Streamlit processes
    that held compiled files open.
- Retained:
  - Source modules, tests, environment examples, reusable template, audit history,
    architecture/API documentation, and GitHub issue/milestone assets.
- Decision:
  - FastAPI is required and is the intended API routing framework for Vercel.
  - Starlette is historical MVP1 context and a temporary comparison baseline only.
  - New LLM synthesis and `/api/ask` work will be implemented in FastAPI.
- Security note:
  - Windows Application Control must be handled through an approved policy/location,
    WSL2, or Docker. The project will not disable or bypass the policy.
- Follow-up:
  - Install an approved Python 3.12 runtime (or use WSL2/Docker), create a fresh
    environment, and pass the FastAPI/Pydantic import gate before route migration.

## 2026-09-14 - FastAPI Compatibility Workflow And Vercel Entry Point

- Status: implementation complete; local Python execution blocked by Windows policy.
- Goal: make FastAPI the primary MVP2 API without breaking either existing UI.
- Changes:
  - Added `fastapi_app.py` with all twelve verified MVP1 route paths and OpenAPI metadata.
  - Kept the Starlette app unchanged as the behavior reference and fallback.
  - Added `api/index.py` as the Vercel ASGI entry point.
  - Added `vercel.json` deployment exclusions and ignored `.vercel/`/`.uv-cache/`.
  - Added tests for the FastAPI application type, route parity, and OpenAPI paths.
  - Updated startup, architecture, deployment, status, and testing documentation.
- Environment evidence:
  - `uv` found CPython 3.12.10, created `.venv`, and installed FastAPI 0.141.1,
    Pydantic 2.13.5, Pydantic Core 2.46.5, and project dependencies.
  - Windows then denied execution of the registered base `python.exe`, preventing
    import, pytest, API, and UI runtime verification in this session.
  - Ruff executed independently and found one import-order issue; it was corrected.
- Deployment decision:
  - Vercel officially documents FastAPI deployment and generically accepts exported
    ASGI applications, so Starlette is technically supported but is not the target.
- Next verification:
  - Resolve Python execution through approved policy/admin action, WSL2, or Docker;
    rerun Ruff and pytest; launch FastAPI on 8765 and Streamlit on 8501; complete the
    existing-UI acceptance matrix before beginning LLM synthesis.

## 2026-09-15 - Docker Build And FastAPI Acceptance

- Status: FastAPI passed; independent Streamlit image blocked by external package-network failures.
- Symptom: the first deterministic container build failed while downloading package
  metadata from `files.pythonhosted.org` with a pip read timeout.
- Finding:
  - Dependency resolution selected the pinned FastAPI/Pydantic/Starlette versions;
    the failure was network transport, not package compatibility or application code.
- Fix:
  - Added a 180-second pip timeout, ten retries, and a persistent BuildKit pip cache.
- Verification pending:
  - Complete the independent Streamlit container build and UI connectivity check
    when PyPI DNS/SSL transport is stable.
- Retry result:
  - Downloads progressed through the full dependency set, but pip rejected one
    corrupted artifact because its SHA-256 did not match the package index metadata.
  - Split the Dockerfile into independent `api` and `streamlit` targets with separate
    caches so the large UI dependency set cannot block FastAPI verification.
- Verification:
  - The isolated FastAPI image built successfully.
  - In-image OpenAPI parity found all 11 API paths with none missing.
  - Vercel `api.index:app` imported as `FastAPI`.
  - The retained fallback imported as `Starlette` with 12 routes.
  - `/`, `/docs`, and `/openapi.json` returned HTTP 200.
  - `/api/status` returned HTTP 200 with MongoDB connected, 125 documents, and the
    Atlas vector index READY/queryable.
  - Live FastAPI search returned three candidates above the configured threshold.
  - Live FastAPI reranking returned all three candidates with both scores; the top
    result had vector score `0.7535` and rerank score `0.71875`.
  - Ruff passed across `src`, `tests`, `api`, and the Streamlit client.
- Remaining block:
  - The Streamlit target repeatedly failed while downloading from PyPI because of
    DNS failures, TLS EOF errors, and one corrupted partial artifact rejected by pip
    hash verification. The separate API target remains healthy and running.

## 2026-09-16 - Current-State And Relevance Reconciliation

- Status: completed.
- Goal: establish one accurate handoff before LLM, Drive, Vercel, and portfolio work.
- Cleanup:
  - Removed regenerated `.notebook`, `.vscode`, and package `egg-info` artifacts.
  - Retained ignored `.venv` and `.uv-cache` directories because they support local
    dependency recovery and are not publishing assets.
- Documentation decisions:
  - FastAPI runtime parity is complete, but native typed Pydantic contracts are not.
  - Grounded LLM answers and `/api/ask` remain the active MVP2 implementation goal.
  - Google Drive source synchronization and Vercel deployment precede portfolio
    Profile Agent integration.
  - `docs/project-status.md` remains the single current-state source of truth;
    chronological audit entries are intentionally preserved as history.
- Google Drive boundary:
  - Use read-only approved-folder access, explicit preview/confirm approval, file
    revision/checksum tracking, and secret-free repository configuration.
- Verification:
  - Removed the regenerated source bytecode cache.
  - Installed pytest/httpx only inside a disposable Linux API container.
  - Current full suite passed: 25 tests in 5.53 seconds.
## 2026-10-25 - Portfolio Chat Integration And Vercel Handoff

- Status: documentation updated; implementation/deployment acceptance pending.
- Goal: align the portfolio and MongoDB RAG docs around adding and testing website chat through the existing FastAPI answer endpoint.
- Evidence:
  - FastAPI registers POST /api/ask and delegates to the answer handler.
  - The handler retrieves, reranks, selects evidence, invokes the chat model, and validates citations.
  - api/index.py and vercel.json already exist.
  - Project status marks Vercel prepared but not deployed and portfolio integration not started.
- Changes: documented the API contract, Vercel preview sequence, secret/CORS/rate-control boundaries, browser fallback behavior, and acceptance tests.
- Verification: source and documentation inspection only. No provider invocation, Vercel deployment, or website browser test was run.
- Follow-up: add /api/ask route/OpenAPI test coverage; run local provider acceptance; deploy preview; add CORS and public-request controls; connect and test the portfolio; record results before production.
- LLM acceptance detail: require a real configured provider call and a multi-chunk synthesis query, then check evidence-only answer content, citation resolution, insufficient-evidence behavior, malformed output, and provider failures. Retrieval-only success does not close this gate.

## 2026-10-25 - Live Ask Provider Access Check

- Status: blocked; live answer acceptance did not pass.
- Goal: verify the website-chat prerequisite by sending a multi-topic profile question through the existing FastAPI `/api/ask` route with OpenAI chat generation.
- Scope: running `mongodb_rag-api` container, MongoDB retrieval, configured OpenAI provider.
- Evidence:
  - `/api/status` reported MongoDB healthy; the local API had OpenAI selected but no `CHAT_MODEL` configured.
  - For this isolated check only, `CHAT_MODEL=gpt-5-mini` was supplied to the request process; project configuration was not changed.
  - The `/api/ask` route returned HTTP 502: OpenAI reported that the project did not have access to `gpt-5-mini` (`model_not_found`).
  - The credential-authenticated model list showed `gpt-5.1`, `gpt-5.5`, and `o4-mini` among the accessible chat-model IDs.
- Verification: route reached the provider adapter, but no generated answer or citations were returned. This does not confirm LLM reasoning, citation quality, or end-to-end chat success.
- Follow-up: select an accessible model, run the same multi-chunk query once, then verify evidence count and citation resolution. Record the successful result before connecting the public portfolio chat.

## 2026-10-25 - Live Ask Retry With gpt-5.1

- Status: blocked; the model was reached but `/api/ask` did not accept its response.
- Goal: retry the same multi-topic profile query using an OpenAI model confirmed available to the configured project.
- Scope: existing FastAPI `/api/ask` route and OpenAI chat adapter; model selection was supplied only to the isolated test process.
- Evidence: the route returned HTTP 502 with `The model response must be a JSON object.` The response contained no accepted answer or citations. This is distinct from the prior gpt-5-mini access denial.
- Verification: provider invocation occurred, but response validation failed; grounded answer generation and citation resolution remain unverified.
- Follow-up: inspect or enforce provider-supported structured JSON output, then rerun the same question and validate multi-chunk evidence and citation mapping before calling the integration successful.

## 2026-10-25 - Structured Output Fix And Retest Gate

- Status: partially fixed; runtime verification pending.
- Symptom: an accessible OpenAI model was invoked, but the prompt-only response failed JSON parsing and `/api/ask` returned HTTP 502.
- Suspected cause: answer generation relied on instructions alone instead of constraining output to the response schema.
- Changes:
  - `src/mongodb_vector_test_ui/llm/grounding.py`: added the Pydantic `GroundedAnswer` schema.
  - `src/mongodb_vector_test_ui/llm/answering.py`: requests LangChain structured output and serializes the schema before applying existing citation checks.
  - `tests/test_answering.py`: added mocked LangGraph workflow coverage for mapping and Pydantic structured responses.
- Verification: Python AST syntax checks passed for the changed modules and new test. Focused tests and live retest were not run because approval to build an isolated API image was denied; the running API container remains untouched.
- Follow-up: obtain approval for the isolated build, run the focused regression test, deploy the patched source only to a temporary local container, then retry `/api/ask` once with `gpt-5.1` and validate evidence/citation resolution.
