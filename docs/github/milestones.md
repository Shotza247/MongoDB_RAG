# GitHub Milestones

Use this file as the source list for GitHub milestones. Create the milestones first, then add issues from `docs/github/issues-mvp1.md` and `docs/github/issues-mvp2.md`.

## MVP1 - Retrieval Foundation

Description:

Build and document the reproducible document-to-MongoDB Vector Search foundation. MVP1 proves document extraction, chunking, embeddings, vector storage, vector search, local UI testing, environment diagnostics, and architecture documentation.

Exit criteria:

- Document ingestion works from upload, drag/drop, file picker, local path, and pasted text.
- Extracted text can be reviewed before chunking.
- Chunks can be previewed before embedding.
- Chunk, embed, and store writes to MongoDB Atlas.
- MongoDB Vector Search returns relevant ranked chunks.
- README, architecture, smoke tests, and audit logs are complete.

## MVP2 - FastAPI And Grounded LLM Answers

Description:

First port the verified retrieval contract to FastAPI and validate both existing UIs.
Then add a query/chat API where vector search provides evidence, a reranker reorders
retrieved chunks, and an LLM generates concise cited answers.

Current progress: FastAPI runtime parity, the Vercel entry point, MongoDB retrieval,
Voyage reranking, and automatic Streamlit score comparison are complete. Native
typed FastAPI contracts, final Streamlit acceptance, best-3-5 selection, `/api/ask`,
grounded generation, and citation verification remain open.

Exit criteria:

- Existing MVP1 routes run under FastAPI with typed contracts and OpenAPI docs.
- Existing browser and Streamlit UIs pass against the FastAPI service.
- The FastAPI app has a Vercel-compatible entry point.
- `/api/ask` or `/api/chat` endpoint exists.
- Retrieval tool returns top candidate chunks.
- Reranker can reorder retrieved chunks.
- LLM uses the best 3-5 chunks as grounded context.
- Answer includes citations to source chunks.
- UI shows answer, citations, and retrieval diagnostics.

## MVP3 - Profile Agent API And Production Readiness

Description:

Add controlled Google Drive source synchronization, deploy the FastAPI service to
Vercel, and turn the lab into a secured Profile Agent backend for the portfolio.

Exit criteria:

- Hosted API works.
- Google Drive uses a read-only approved-folder scope with explicit sync approval.
- File revision/checksum tracking prevents unchanged documents from being re-embedded.
- Secrets are managed outside the repo.
- CORS/auth strategy is documented.
- Portfolio chatbot can call the API.
- Logs and audit trail are available.
- Deployment smoke checks are documented.
