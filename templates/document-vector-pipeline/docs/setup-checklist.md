# Setup Checklist

## 1. Create Project

- Create a clean repository.
- Add `src/`, `scripts/`, `tests/`, `docs/`, and `data/source_documents/`.
- Add `.gitignore`.
- Copy `.env.example` to `.env`.
- Keep `.env` out of Git.

## 2. Configure MongoDB

- Create a MongoDB Atlas database.
- Create a collection for document chunks.
- Add the connection string to `MONGODB_URI`.
- Confirm your IP/network access allows the app to connect.
- Confirm the database user has read/write permissions.

## 3. Configure Embeddings

- For MongoDB Atlas Model API keys:
  - `EMBEDDING_PROVIDER=voyage`
  - `VOYAGE_BASE_URL=https://ai.mongodb.com/v1`
  - `VOYAGE_MODEL=voyage-context-4`

- For direct Voyage keys:
  - `EMBEDDING_PROVIDER=voyage`
  - `VOYAGE_BASE_URL=https://api.voyageai.com/v1`

- For OpenAI:
  - `EMBEDDING_PROVIDER=openai`
  - `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`

- For local plumbing tests:
  - `EMBEDDING_PROVIDER=hashing`

## 4. Add Documents

- Add TXT, MD, Markdown, CSV, JSON, HTML, PDF, or DOCX files to the source document folder.
- Start with one trusted document.
- Avoid private or sensitive files until `.gitignore` is confirmed.

## 5. Run Local Tests

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q
```

## 6. Start The Test UI

```powershell
python -m uvicorn <package>.app:app --host 127.0.0.1 --port 8765 --http h11
```

## 7. Browse MongoDB Targets

- Load visible databases.
- Select the database for the current RAG implementation.
- Load collections for that database.
- Select the collection to inspect or use.
- Inspect the collection summary.
- Confirm document count, regular indexes, search indexes, and sample fields look correct.

## 8. Run Document Extraction

- Use drag/drop or file picker for browser upload extraction.
- Use local file-path extraction for documents already on disk.
- Confirm extracted text appears in the document text box.
- Check that extracted text is readable before spending embedding calls.

## 9. Preview Chunks

- Click `Preview Chunks`.
- Confirm chunk count and chunk text look reasonable.
- Adjust source text before embedding if extraction is noisy.

## 10. Run Chunk, Embed, And Store

- Click `Chunk, Embed, and Store`.
- Confirm chunks created equals embeddings created equals inserted records.
- Confirm the vector index is created or already exists.

## 11. Run Vector Search

- Ask a query related to the ingested document.
- Confirm the best source appears near the top.
- Inspect scores and source metadata.

## Legacy Script Ingestion

```powershell
python scripts\ingest_profile.py
```

Expected output shape:

```text
Loaded 1 documents and created N chunks.
Created N embeddings with provider=voyage.
Inserted N chunks into DB.COLLECTION.
Vector index requested/verified: INDEX_NAME
```

## API Locally

```powershell
python -m uvicorn profile_agent.api:app --host 127.0.0.1 --port 8765 --http h11
```

## Test API

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8765/health"

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8765/ask" `
  -ContentType "application/json" `
  -Body '{"question":"What does this document say?","top_k":3}'
```
