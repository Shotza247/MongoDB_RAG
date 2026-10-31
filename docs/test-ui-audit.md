# Test UI Audit

## 2026-09-15 - FastAPI Existing-Contract Acceptance

- FastAPI is now the primary MVP2 API; Starlette remains the MVP1 fallback/reference.
- The FastAPI Linux image built and exposed all existing API paths through OpenAPI.
- Root browser UI, Swagger docs, OpenAPI JSON, MongoDB status, vector search, and
  Voyage reranking passed over HTTP on port `8765`.
- Streamlit labels/default URL were made framework-neutral and now target port `8765`.
- The independent Streamlit container build remains pending because PyPI repeatedly
  failed Altair/pyarrow downloads with DNS and TLS transport errors.
- No Streamlit application regression was observed in static Ruff verification.

## 2026-09-06 - Reusable API Documentation Closeout

- Status: passed
- Goal: Make the MVP1 endpoint documentation understandable and reusable so future projects can clearly see which endpoints exist and what each one does.
- Scope:
  - `README.md`
  - `docs/api-reference.md`
  - `docs/architecture/mvp1-architecture.md`
  - `templates/document-vector-pipeline/README.md`
  - `templates/document-vector-pipeline/docs/api-reference.md`
  - `templates/document-vector-pipeline/scripts/smoke-test-commands.md`
  - `templates/document-vector-pipeline/scripts/update_vector_index.py`
- Changes:
  - Added a full MVP1 API reference describing endpoint flow, target selection, route purposes, request examples, response evidence, retrieval controls, and future FastAPI naming notes.
  - Added a template API reference with project-neutral placeholders for future RAG projects.
  - Added README endpoint tables so `/api/index/document` is clearly identified as the full chunk, embed, and store endpoint.
  - Expanded the MVP1 architecture API surface with inputs, output evidence, and endpoint purpose.
  - Added reusable smoke-test flow notes that show the expected order from status checks through vector search.
  - Added a standalone template `scripts/update_vector_index.py` so copied projects can update Atlas Vector Search filter paths without importing the reference app package.
- Evidence:
  - `/api/document/chunks` is documented as preview-only.
  - `/api/index/document` is documented as the write path that chunks reviewed text, embeds chunks, replaces chunks with the same `source_id`, stores vectors, and creates/checks the vector index.
  - `/api/search` is documented as query embedding plus MongoDB vector retrieval with `top_k`, `min_score`, `num_candidates`, exact mode, and filters.
- Verification:
  - Documentation references were checked with `rg`.
  - Ruff and Python compile checks were run after documentation/script updates.
- Follow-up:
  - During MVP2, migrate the production-style hosted API contract toward clearer FastAPI route names such as `/api/rag/ingest` and `/api/rag/search`.

## 2026-09-05 - Reusable Template Second Collection Smoke Test

- Status: passed
- Goal: Confirm the MVP1 reusable template approach works cleanly against a second MongoDB collection while still using the Starlette test UI.
- Scope:
  - `RAG_with_MongoDB.mvp1_template_smoke_chunks`
  - `profile_vector_index`
  - Starlette local API at `http://127.0.0.1:8767`
  - Voyage embeddings through MongoDB Atlas Model API
- Evidence:
  - Target collection started reachable with `mongo_ok: True`, `document_count: 0`, and no search indexes.
  - Indexed synthetic source `mvp1-template-smoke-test`.
  - Created `1` chunk, created `1` Voyage embedding, and inserted `1` MongoDB document.
  - Created/updated `profile_vector_index` for the second collection.
  - Atlas reported the second collection index as `READY` and `queryable: True`.
  - Verified filter paths: `metadata.source_id`, `metadata.title`, `metadata.section`, and `chunk_id`.
  - Plain vector search returned `mvp1-template-smoke-test` with score about `0.7569`.
  - Source ID plus title filtered search returned the same source with score about `0.7363`.
  - Chunk ID filtered search for `abbda4f00d415e1dc46367f3` returned the expected chunk with score about `0.6935`.
  - Collection summary reported `document_count: 1`, source ID `mvp1-template-smoke-test`, and title `MVP1 Reusable Template Smoke Test`.
- Verification:
  - Second collection ingestion: passed.
  - Second collection vector index readiness: passed.
  - Second collection retrieval controls: passed.
  - Second collection filter compatibility: passed.
- Decision:
  - MVP1 reusable-template validation can use the Starlette test UI.
  - The final hosted reusable API can still migrate to FastAPI in MVP2 for typed request models and OpenAPI docs.
- Follow-up:
  - User can complete manual UI acceptance testing against `mvp1_template_smoke_chunks`.
  - After manual acceptance, MVP1 can be closed and MVP2 can begin with reranking and grounded LLM answers.

## 2026-09-05 - Atlas Vector Search Index Closeout

- Status: passed
- Goal: Complete MVP1 closeout item 1 by updating the live Atlas Vector Search index so all intended retrieval filters are usable from the test UI.
- Scope:
  - `RAG_with_MongoDB.profile_chunks`
  - `profile_vector_index`
  - `scripts/update_vector_index.py`
  - `src/mongodb_vector_test_ui/vector_store.py`
  - `tests/test_vector_store.py`
  - `README.md`
  - `docs/architecture/mvp1-architecture.md`
- Changes:
  - Added a reusable `scripts/update_vector_index.py` command for creating or updating the Atlas Vector Search index from the shared MVP1 definition.
  - Added shared vector-index definition helpers to `MongoVectorStore`.
  - Updated the live Atlas index in place with `metadata.source_id`, `metadata.title`, `metadata.section`, and `chunk_id` filter paths.
  - Added a unit test to keep the shared index definition aligned with `FILTER_FIELDS`.
- Evidence:
  - Before update, the live index only exposed `metadata.section` and `metadata.source_id` as filter paths.
  - After update, the live index exposed `chunk_id`, `metadata.section`, `metadata.source_id`, and `metadata.title`.
  - Atlas reported the index as `READY` and `queryable: True`.
  - `chunk_id=5319d67877c8fc34ba66e3c6` filtered search returned the expected `document-ingestion-smoke-test` chunk with score about `0.7535`.
  - `metadata.title=Document Ingestion Smoke Test` filtered search returned the expected chunk with score about `0.7060`.
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest`: `11 passed in 0.85s`.
  - `.\.venv\Scripts\python.exe -m ruff check .`: passed.
  - `.\.venv\Scripts\python.exe -m py_compile scripts\update_vector_index.py src\mongodb_vector_test_ui\vector_store.py`: passed.
- Follow-up:
  - User can now complete MVP1 closeout item 2 by manually acceptance-testing the UI filters and retrieval controls.

## 2026-09-05 - Retrieval Controls Added To Test UI

- Status: implemented and smoke-tested
- Goal: Add second-pass retrieval controls so vector search can be tuned before MVP2 LLM answering and reranking.
- Scope: local MongoDB Vector Search test UI and reusable document-vector pipeline template.
- Changes:
  - Added `top_k`, minimum similarity score, `numCandidates`, exact nearest-neighbor mode, and metadata filters to the Vector Search UI.
  - Added source ID, title, section, and chunk ID filter inputs.
  - Mapped source ID filtering to `metadata.source_id`, matching the current stored chunk schema.
  - Added score thresholding after `$vectorSearch`, so `top_k` is now the maximum result count and low-score results below the selected threshold are excluded.
  - Added preflight diagnostics for unsupported filter paths, so the UI returns a clear message when the selected MongoDB Vector Search index does not include a requested filter field.
  - Updated the desired reusable vector index definition to include `metadata.source_id`, `metadata.title`, `metadata.section`, and `chunk_id` as filter fields.
  - Updated README, MVP1 architecture, MVP2 preview, and template smoke-test documentation.
- Evidence:
  - Current live index filter paths: `metadata.source_id`, `metadata.section`.
  - Unfiltered search with `min_score=0.6` and `numCandidates=150` returned `document-ingestion-smoke-test` with score about `0.8066`.
  - Source ID filtered search for `document-ingestion-smoke-test` returned the same top result.
  - Exact search mode returned the same top result and omitted `numCandidates`, as expected.
  - Chunk ID filtering returned a clear compatibility error because the current live index does not yet include `chunk_id` as a filter field.
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest`: `10 passed in 0.79s`.
  - `.\.venv\Scripts\python.exe -m ruff check .`: passed.
  - Python compile check passed for `src/mongodb_vector_test_ui/app.py` and `src/mongodb_vector_test_ui/vector_store.py`.
- Follow-up:
  - Completed on 2026-09-05: live Atlas index now includes all desired filter paths.
  - Add richer metadata during ingestion, such as section, document type, role family, skill area, and source version, so filtering becomes useful beyond single-document experiments.

## 2026-09-04 - MongoDB Database And Collection Browser Added

- Status: passed
- Goal: make the reusable RAG test UI able to browse existing MongoDB databases and collections, inspect collection summaries, and target selected collections for indexing/search without editing `.env`.
- Scope:
  - `src/mongodb_vector_test_ui/app.py`
  - `src/mongodb_vector_test_ui/config.py`
  - `src/mongodb_vector_test_ui/vector_store.py`
  - `tests/test_config.py`
  - `README.md`
  - `docs/architecture/mvp1-architecture.md`
  - `docs/architecture/project-structure.md`
  - `templates/document-vector-pipeline/`
- Evidence:
  - Added `/api/mongodb/databases`.
  - Added `/api/mongodb/collections`.
  - Added `/api/mongodb/collection/summary`.
  - Added a `MongoDB Browser` panel to the test UI with database selection, collection selection, and collection summary inspection.
  - Updated status, index creation, document storage, and vector search routes to accept selected database/collection targets.
  - Collection summary now returns partial diagnostics if index/sample-field lookup fails, instead of failing the whole browser panel.
- Changes:
  - `config.py`: added safe target override validation for selected database and collection names.
  - `vector_store.py`: added database listing, collection listing, and collection summary methods.
  - `app.py`: added DB browser endpoints and UI controls.
  - `tests/test_config.py`: added safe target validation tests.
  - Template docs now include DB/collection browsing in the reusable MVP1 checklist, smoke tests, and audit fields.
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest`: `7 passed`.
  - `.\.venv\Scripts\python.exe -m ruff check .`: `All checks passed!`.
  - Syntax check passed for updated app/config/vector store modules.
  - Live smoke on `http://127.0.0.1:8767`: database browser found 3 visible databases.
  - Live smoke on `http://127.0.0.1:8767`: collection browser found 1 collection for `RAG_with_MongoDB`.
  - Live smoke on `http://127.0.0.1:8767`: collection summary for `RAG_with_MongoDB.profile_chunks` showed 119 documents and 1 search index.
  - Live selected-target status returned `mongo_ok: True` for `RAG_with_MongoDB.profile_chunks`.
- Follow-up:
  - User should test the browser panel with additional databases/collections before we add retrieval-quality controls such as metadata filters, exact search, and reranking.

## 2026-09-01 - Mermaid Architecture Diagrams Added

- Status: passed
- Goal: add GitHub-renderable Mermaid architecture diagrams to the main MVP documentation.
- Scope:
  - `README.md`
  - `docs/architecture/mvp1-architecture.md`
  - `docs/architecture/mvp2-preview.md`
  - `docs/architecture/project-structure.md`
- Evidence:
  - README now includes a high-level MVP1 retrieval architecture snapshot with MVP2 reranking/LLM handoff.
  - MVP1 architecture now includes a system context diagram, request sequence diagram, and MVP2 transition diagram.
  - MVP2 preview now includes a target reranking/LLM flow diagram and ask/chat sequence diagram.
  - Project structure now includes a repository map showing runtime code, scripts, docs, templates, GitHub metadata, and ignored local files.
- Changes:
  - Added Mermaid `flowchart` and `sequenceDiagram` blocks.
  - Used GitHub-friendly `<br/>` label breaks in Mermaid nodes.
- Verification:
  - Confirmed Mermaid code fences exist in README and architecture docs.
  - Confirmed no raw `\n` Mermaid label breaks remain in the updated docs.
- Follow-up:
  - Review diagrams on GitHub after pushing to confirm visual layout matches expectations.

## 2026-09-01 - MVP1 Architecture And GitHub Planning Added

- Status: passed
- Goal: document MVP1 architecture, define the project structure, and create GitHub-ready milestones/issues for MVP1 and MVP2 planning.
- Scope:
  - `docs/architecture/mvp1-architecture.md`
  - `docs/architecture/mvp2-preview.md`
  - `docs/architecture/project-structure.md`
  - `docs/github/milestones.md`
  - `docs/github/issues-mvp1.md`
  - `docs/github/issues-mvp2.md`
  - `docs/github/project-board.md`
  - `docs/github/gh-cli-import.md`
  - `.github/ISSUE_TEMPLATE/`
  - `scripts/create_github_mvp_plan.ps1`
  - `templates/document-vector-pipeline/`
  - `README.md`
- Evidence:
  - MVP1 architecture now defines the retrieval foundation, API surface, MongoDB record shape, boundaries, and verification baseline.
  - MVP2 preview now defines reranking, selected evidence chunks, LLM grounded answer generation, citations, and ask/chat API planning.
  - GitHub planning docs now include milestones, MVP1 issues, MVP2 issues, and a project board description.
  - GitHub issue templates now exist for MVP tasks and bug/error reports.
  - MVP1 document-vector pipeline template now reflects document extraction, extracted text review, chunk preview, vector storage, and retrieval testing.
- Changes:
  - Added GitHub CLI helper script for labels, milestones, and starter issues.
  - Added project structure documentation to support GitHub publishing.
  - Updated README with architecture/planning links and feature log entry.
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest`: `4 passed`.
  - `.\.venv\Scripts\python.exe -m ruff check .`: `All checks passed!`.
  - `powershell -ExecutionPolicy Bypass -File .\scripts\create_github_mvp_plan.ps1 -DryRun`: printed expected `gh label`, `gh milestone`, and `gh issue create` commands.
  - `.gitignore` confirmed `.env`, `.env.*`, `.venv/`, caches, egg-info, private source docs, logs, and editor folders are excluded.
- Follow-up:
  - Initialize the folder as a Git repo, push to GitHub, then run `.\scripts\create_github_mvp_plan.ps1 -DryRun` followed by the live script when ready.

## 2026-09-01 - Document Ingestion Pipeline Added To Test UI

- Status: passed
- Goal: Let a user load a document into the test UI, inspect extracted text, preview chunks, then chunk, embed, and store the document in MongoDB Vector Search.
- Scope:
  - `src/mongodb_vector_test_ui/app.py`
  - `src/mongodb_vector_test_ui/document_extraction.py`
  - `src/mongodb_vector_test_ui/chunking.py`
  - `pyproject.toml`
  - `tests/test_document_extraction.py`
  - `README.md`
- Evidence:
  - Added extraction support for TXT, Markdown, CSV, JSON, HTML, DOCX, and PDF.
  - Added drag/drop and file picker flow through `/api/document/extract/upload`.
  - Added local file-path extraction through `/api/document/extract/path`.
  - Added chunk preview through `/api/document/chunks`.
  - Kept `Chunk, Embed, and Store` on the existing `/api/index/document` endpoint so the MongoDB write path stays unchanged.
- Changes:
  - `document_extraction.py`: added safe extraction, 12 MB test UI file limit, DOCX XML parsing, PDF extraction through `pypdf`, text normalization, and source metadata.
  - `app.py`: added document extraction endpoints, chunk preview endpoint, drag/drop UI, file-path UI, extracted text review, and chunk preview output.
  - `pyproject.toml`: added `pypdf>=5.0`.
  - `tests/test_document_extraction.py`: added TXT normalization and DOCX extraction coverage.
  - `README.md`: documented the new ingestion workflow and supported file types.
- Verification:
  - `.\.venv\Scripts\python.exe -m pip install -e .`: installed updated dependencies including `pypdf-6.16.2`.
  - `.\.venv\Scripts\python.exe -m pytest`: `4 passed`.
  - `.\.venv\Scripts\python.exe -m ruff check .`: `All checks passed!`.
  - Python syntax check passed for updated app modules.
  - Live local API smoke on `http://127.0.0.1:8766`: path extraction returned 133 characters, upload extraction returned 133 characters, chunk preview returned 1 chunk.
  - Live `Chunk, Embed, and Store` smoke inserted 1 chunk with Voyage model `voyage-context-4` into MongoDB Vector Search index `profile_vector_index`.
  - Live vector search smoke returned 3 results, with `document-ingestion-smoke-test` as the top result.
- Follow-up:
  - Next phase: add LLM reasoning, retrieved-context answer generation, reranking, and source-grounded response evaluation.

## 2026-09-01 - UI Smoke Test Passed And Reusable Audit Skill Added

- Status: passed
- Goal: Confirm the MongoDB Vector Search test UI is working and create a reusable audit-log skill for future errors, fixes, and verification trails.
- Scope:
  - `C:\Users\Jabulani Ndlovu\.codex\skills\audit-log\SKILL.md`
  - `C:\Users\Jabulani Ndlovu\.codex\skills\audit-log\scripts\append_audit.py`
  - `docs/test-ui-audit.md`
- Evidence:
  - User confirmed the UI test now works perfectly.
  - New Codex personal skill `audit-log` was created for project audit logs, setup notes, pipeline troubleshooting, and verification milestones.
  - Skill validation passed with `Skill is valid!`.
  - Helper smoke test appended a temporary audit entry successfully.
- Changes:
  - Added reusable `audit-log` skill guidance for choosing `BUG_AUDIT.md`, `PIPELINE_AUDIT.md`, `DEPLOYMENT_AUDIT.md`, `PROJECT_AUDIT.md`, or an existing project audit file.
  - Added `scripts/append_audit.py` helper for quick append-only audit entries without recording secrets.
  - Tightened the Windows example command so paths with spaces work correctly.
- Verification:
  - `python "C:\Users\Jabulani Ndlovu\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "C:\Users\Jabulani Ndlovu\.codex\skills\audit-log"`: passed.
  - Temporary helper smoke test wrote `PROJECT_AUDIT.md` and included the expected title, status, goal, evidence, and verification fields.
- Follow-up:
  - Use the `audit-log` skill whenever future MongoDB, Voyage, OpenAI, hosting, ingestion, or Profile Agent errors need a reproducible trail.

## 2026-08-31 - MongoDB Vector Search Test UI

- Status: implemented, local UI verified, pending `.env` restoration for MongoDB-backed indexing/search
- Goal: Build a small reproducible UI for testing MongoDB Vector Search indexing and querying with the same embedding providers used by the Profile Agent.
- Scope:
  - `src/mongodb_vector_test_ui/app.py`
  - `src/mongodb_vector_test_ui/vector_store.py`
  - `src/mongodb_vector_test_ui/embeddings.py`
  - `src/mongodb_vector_test_ui/chunking.py`
  - `src/mongodb_vector_test_ui/config.py`
  - `tests/`
- Embedding providers:
  - Voyage through MongoDB Atlas Model API: `https://ai.mongodb.com/v1`
  - OpenAI embeddings through direct REST
  - Hashing embeddings for local plumbing tests only
- UI capabilities:
  - MongoDB status check
  - Vector index create/check
  - Paste-text document indexing
  - Query embedding and `$vectorSearch`
  - Score/result inspection
- Decisions:
  - Use Starlette instead of FastAPI to avoid Pydantic native DLL issues seen on the local Windows environment.
  - Use direct REST instead of Voyage/OpenAI SDKs to avoid unnecessary transitive dependencies in the smoke-test path.
  - Keep this UI as a test lab, not the production Profile Assistant frontend.
- Verification:
  - Python syntax parse passed for 8 source/test files.
  - Dependency install succeeded in `.venv`.
  - Tests passed with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`: `2 passed in 0.41s`.
  - App import passed: `Starlette`.
  - Runtime config showed `RAG_with_MongoDB.profile_chunks`, provider `voyage`, base URL `https://ai.mongodb.com/v1`, model `voyage-context-4`.
  - UI page returned HTTP 200 at `http://127.0.0.1:8765`.
  - `/api/status` responded and correctly reported `MONGODB_URI is required` because the cleaned repo does not currently have a private `.env`.
- Next verification:
  - Restore/copy `.env` from `.env.example` and add `MONGODB_URI` plus `VOYAGE_API_KEY`.
  - Start the UI again.
  - Check `/api/status`, create/check index, index sample text, and search.

## 2026-08-31 - Env Placeholder and Missing Key Diagnostics

- Status: fixed in tooling, pending user `.env` value update
- Symptom:
  - `Error: The DNS query name does not exist: _mongodb._tcp.cluster.mongodb.net.`
  - `Error: VOYAGE_API_KEY is required for Voyage embeddings.`
- Scope: local test UI environment configuration.
- Suspected cause: the project root `.env` currently being loaded still contains a placeholder MongoDB hostname and an empty Voyage key.
- Evidence:
  - Safe `.env` scan showed `MONGODB_HOST=CLUSTER.mongodb.net`.
  - Safe `.env` scan showed `VOYAGE_API_KEY=<empty>`.
- Changes:
  - `src/mongodb_vector_test_ui/config.py`: added project-root `.env` loading, safe diagnostics, MongoDB host detection, and config validation.
  - `src/mongodb_vector_test_ui/app.py`: added `config_issues` to `/api/status`.
  - `scripts/check_env.py`: added safe command-line env validation.
  - `.env.example`: changed the MongoDB placeholder to `cluster0.xxxxx.mongodb.net` and made the Voyage key placeholder explicit.
  - `README.md`: added troubleshooting steps for the current errors.
- Verification:
  - Pending: run `python scripts\check_env.py` after updating `.env`.
- Follow-up:
  - Replace the current `.env` placeholder values with the real Atlas connection string and real Atlas Model API key.

## 2026-08-31 - Real MongoDB URI Found In Another Project Env

- Status: fixed in diagnostics, pending value copy into this project `.env`
- Symptom: User had a valid URI shaped like `cluster0.aebju2f.mongodb.net`, but `scripts/check_env.py` still reported `cluster.mongodb.net`.
- Scope: local environment configuration for MongoDB Vector Search Test UI.
- Suspected cause: user updated a different `.env` file than the one loaded by this app.
- Evidence:
  - Safe search found the real hostname in `C:\Users\Jabulani Ndlovu\Downloads\Project Folder\Project Folder\Idea_Not_Started\Profile Agent Architecture Service\.env`.
  - The test UI loads `C:\Users\Jabulani Ndlovu\Downloads\Project Folder\Project Folder\Idea_Not_Started\MongoDB_RAG\.env`.
- Changes:
  - `src/mongodb_vector_test_ui/config.py`: added `env_file` to safe diagnostics.
  - `src/mongodb_vector_test_ui/config.py`: set `load_dotenv(..., override=True)` so the project `.env` wins over stale shell variables.
  - `README.md`: clarified that the test UI uses the root `MongoDB_RAG\.env`, not `.env.example` or another project `.env`.
- Verification:
  - Pending: copy the real `MONGODB_URI` and `VOYAGE_API_KEY` into `MongoDB_RAG\.env`, then run `python scripts\check_env.py`.
- Follow-up:
  - Restart the UI after editing `.env`; running servers do not reload environment changes automatically.

## 2026-08-31 - Malformed MongoDB URI Diagnostic

- Status: fixed in checker, pending `.env` correction
- Symptom: `scripts/check_env.py` reported `mongodb_uri_set: True` but `mongodb_host:` was blank.
- Scope: local `.env` validation for MongoDB Vector Search Test UI.
- Suspected cause: the `MONGODB_URI` value in `MongoDB_RAG\.env` is not the full Atlas connection string.
- Evidence:
  - Safe structure check showed `MONGODB_URI` length was 28 characters.
  - Safe structure check showed it did not start with `mongodb+srv://` or `mongodb://`.
  - Safe structure check showed it contained no `@`.
- Changes:
  - `src/mongodb_vector_test_ui/config.py`: added safe URI length, scheme, and `@` count diagnostics.
  - `src/mongodb_vector_test_ui/config.py`: changed validation to report malformed URI separately from placeholder host.
- Verification:
  - Pending: replace `MONGODB_URI` with the full Atlas connection string, then rerun `python scripts\check_env.py`.
- Follow-up:
  - Make sure `.env` contains the real URI in one line with no angle brackets and URL-encoded password characters.

## 2026-09-12 - Live Streamlit Rerank Score Verification

- Status: passed.
- Symptom: vector scores were visible, but the user had not seen a numerical rerank score.
- Cause: reranking is a separate manual test action; the initial result correctly showed `Rerank: Not run`, and the network request plus Streamlit rerun required additional wait time.
- Evidence:
  - Live `/api/status` returned HTTP 200 with MongoDB and reranker configuration healthy.
  - Live `/api/rerank` returned vector and rerank scores for every candidate.
  - Browser acceptance rendered `Vector 0.665`, `Rerank 0.445`, and `Reranked all 1 retrieved candidates`.
- Change:
  - Added an explicit message directing users to **Rerank retrieved chunks** and explaining the `Not run` state.
- Verification:
  - Full pytest suite: 22 passed.
  - Full Ruff check and Python compilation: passed.
- Follow-up:
  - Keep reranking manual until best-3-5 selection and `/api/ask` integrate the retrieval stages.

## 2026-09-12 - Automatic Reranking Supersedes Manual UI Flow

- Status: passed.
- Scope: Streamlit ranked retrieval workflow.
- Change:
  - A query submission now runs MongoDB vector search and then Voyage reranking automatically.
  - The previous manual-only flow is retained in this log as history; the current UI uses **Rerun reranking** or **Retry reranking** after the automatic attempt.
- Verification:
  - Fresh browser query displayed `Vector 0.732`, `Rerank 0.715`, and `Reranked all 1 retrieved candidates` without pressing a rerank button.
  - **Rerun reranking** and both raw endpoint responses remained available.

## 2026-09-16 - Domain Architecture And FastAPI Entry Point

- Status: passed.
- Goal: reorganize the working RAG service by responsibility and confirm that
  FastAPI remains the primary runtime.
- Scope: runtime package, scripts, tests, Docker, Vercel entry point, README, and
  architecture documentation.
- Changes:
  - Moved API applications to `src/mongodb_vector_test_ui/api/fastapi.py` and
    `src/mongodb_vector_test_ui/api/starlette.py`.
  - Moved domain code under `core`, `ingestion`, `chunking`, `embeddings`,
    `vectorstore`, `retrieval`, and `llm` packages.
  - Updated every runtime import, test import, launch command, Docker target, and
    Vercel import to the new module paths.
  - Kept Starlette as the explicit MVP1 fallback; FastAPI remains the production,
    Docker, and Vercel application.
  - Omitted empty `utils`, `logs`, and `prompts` folders because they have no
    implemented responsibility yet.
- Evidence:
  - Rebuilt image imports `FastAPI` with the complete route surface and the
    Starlette fallback with all 12 MVP1 routes.
  - Live `/`, `/docs`, `/openapi.json`, and `/api/status` returned HTTP 200.
  - Status reported `mongo_ok: true`, 125 documents, and a READY vector index.
- Verification:
  - Linux container test suite: 25 passed in 14.47 seconds.
  - Ruff: all checks passed after ignoring `EXE002`, which is caused by Windows
    bind mounts presenting files as executable inside Linux.
  - Local `.venv` remains unusable because its launcher references a missing local
    Python 3.12 executable; Docker is the verified development runtime.
- Follow-up:
  - Replace delegated Starlette request parsing with typed FastAPI contracts as the
    next API-hardening step, then implement evidence selection and `/api/ask`.

## 2026-09-17 - Automatic Browser Vector Search And Reranking

- Status: passed.
- Goal: give the FastAPI-hosted browser UI the same automatic retrieval and
  reranking behavior as the Streamlit client.
- Scope: browser query flow in `api/starlette.py`, FastAPI UI contract test, README,
  and project status.
- Changes:
  - Query submission now calls `/api/search` and then `/api/rerank` automatically.
  - Results display MongoDB `vector_score` and Voyage `rerank_score` separately.
  - Raw responses from both endpoints are retained in the browser output panel.
  - Source ID, chunk ID, title, text, and original vector evidence remain attached
    after reranking.
- Verification:
  - Full Linux test suite: 26 passed.
  - Ruff: all checks passed, excluding the documented Windows bind-mount `EXE002`
    permission artifact.
  - Live query returned three candidates and reranked all three.
  - The top live result returned vector score `0.7535057663917542`, rerank score
    `0.71875`, source ID `document-ingestion-smoke-test`, and chunk ID
    `5319d67877c8fc34ba66e3c6`.
- Follow-up:
  - Add best-3-5 evidence selection before grounded LLM synthesis in `/api/ask`.

## 2026-09-17 - README And Feature Log Separation

- Status: passed.
- Goal: make the GitHub landing page easy to understand and reproduce while
  preserving the full implementation history outside the README.
- Scope: `README.md`, `docs/FEATURE_LOG.md`, and project-structure documentation.
- Changes:
  - Rebuilt the README around purpose, current capabilities, process flow,
    architecture, setup, MongoDB preparation, local and Docker execution,
    verification, reuse steps, API summary, roadmap, and security guidance.
  - Moved chronological delivery history into `docs/FEATURE_LOG.md`.
  - Added missing milestones for Voyage reranking, automatic Streamlit reranking,
    FastAPI and Vercel foundations, domain-oriented package structure, and automatic
    reranking in the FastAPI-hosted browser UI.
  - Kept detailed debugging evidence in this audit and current-state evidence in
    `docs/project-status.md` to avoid duplicating their responsibilities.
- Verification:
  - Confirmed the README no longer contains an embedded Feature Log section.
  - Confirmed all linked local documentation files exist.
- Follow-up:
  - Update `docs/FEATURE_LOG.md` whenever a user-facing capability or architecture
    milestone is completed.
## 2026-10-25 - Website Chat API Handoff

- Status: documentation updated; live acceptance pending.
- Evidence: FastAPI contains POST /api/ask; RAG project has api/index.py and vercel.json. Portfolio README still describes its local keyword matcher.
- Decision: deploy the RAG API independently to Vercel preview, test it, then connect the website with structured citations and an explicit local fallback.
- Follow-up: route/OpenAPI assertion, live provider check, preview deployment, exact-origin CORS, rate/target controls, and website browser acceptance.

## 2026-10-25 - Grounded Answer Live Check And Structured-Output Patch

- Status: partially fixed; successful response acceptance is pending.
- Evidence: pre-fix `/api/ask` reached OpenAI; `gpt-5-mini` was unavailable to the project, while `gpt-5.1` returned output rejected by the JSON parser. No valid answer or citations were returned.
- Change: the generation workflow now requests the typed `GroundedAnswer` structured-output contract before running existing citation validation.
- Verification: syntax check passed. The focused test and live retry were not run because approval for the isolated Docker build was denied; the existing service was not replaced.
- Follow-up: run focused regression coverage and one live multi-chunk `/api/ask` test on an isolated patched container, then record response and citation validation results.
