# MVP1 GitHub Issues

These issues are ready to paste into GitHub or create through GitHub CLI after the repo exists.

## Issue 1 - Document MVP1 Retrieval Architecture

Labels: `documentation`, `architecture`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Create a clear MVP1 architecture document showing how documents move through extraction, chunking, embeddings, MongoDB storage, vector search, and UI retrieval.

### Acceptance Criteria

- Architecture doc exists under `docs/architecture/`.
- MVP1 boundaries are explicit.
- API surface is documented.
- MongoDB record shape is documented.
- MVP2 handoff points are identified.

## Issue 2 - Add Document Extraction To Test UI

Labels: `feature`, `ingestion`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Allow users to load a document from drag/drop, file picker, or local file path and extract text into the UI for review before chunking.

### Acceptance Criteria

- Upload extraction endpoint exists.
- File-path extraction endpoint exists.
- UI supports drag/drop and file picker.
- UI supports local file path extraction.
- Extracted text appears in `Document Text`.
- Supported file types are documented.

## Issue 3 - Add Chunk Preview Before Embedding

Labels: `feature`, `retrieval`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Add a preview step so users can inspect chunk count, chunk IDs, metadata, and text before embedding and storing.

### Acceptance Criteria

- Chunk preview endpoint exists.
- UI has a `Preview Chunks` action.
- Preview does not call embedding provider.
- Preview output includes chunk count and chunk text.

## Issue 4 - Verify End-To-End MongoDB Vector Storage

Labels: `testing`, `mongodb`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Verify that reviewed document text can be chunked, embedded with Voyage, and stored in MongoDB Atlas Vector Search.

### Acceptance Criteria

- `Chunk, Embed, and Store` inserts chunks into MongoDB.
- Embedding provider and model are included in the response.
- Vector index create/check still works.
- Verification result is recorded in `docs/test-ui-audit.md`.

## Issue 5 - Verify Vector Search Retrieval

Labels: `testing`, `retrieval`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Confirm MongoDB Vector Search returns relevant ranked chunks for a query against ingested documents.

### Acceptance Criteria

- Query endpoint embeds the query.
- MongoDB `$vectorSearch` returns ranked chunks.
- UI shows scores and source metadata.
- Smoke test confirms the expected source appears as the top result.

## Issue 6 - Complete MVP1 Template Package

Labels: `documentation`, `template`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Update the reusable document-vector pipeline template so future projects can copy the MVP1 setup pattern.

### Acceptance Criteria

- Template README reflects UI-based document ingestion.
- Setup checklist includes document extraction and chunk preview.
- Smoke test commands include test UI routes.
- Audit template includes extraction, storage, and retrieval evidence fields.

## Issue 7 - Prepare Repository For GitHub Publishing

Labels: `repository`, `documentation`, `mvp1`
Milestone: `MVP1 - Retrieval Foundation`

### Description

Prepare the project for GitHub by documenting what should be committed and what should remain local.

### Acceptance Criteria

- README includes publishing notes.
- `.env`, virtual environments, caches, and private source documents are excluded.
- GitHub milestone and issue docs exist.
- No secrets are included in docs.
