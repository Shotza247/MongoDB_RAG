# Smoke Test Commands

Run these from a project root after copying the template pattern.

## Dependency Check

```powershell
python --version
python -m pip install -e ".[dev]"
```

## Unit Tests

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q
```

## Ingestion

```powershell
python scripts\ingest_profile.py
```

## Test UI/API Server

```powershell
python -m uvicorn <package>.app:app --host 127.0.0.1 --port 8765 --http h11
```

## Vector Index Closeout

```powershell
python scripts\update_vector_index.py --database RAG_with_MongoDB --collection profile_chunks --wait
```

## MVP1 API Calls

The intended reusable flow is:

```text
status
  -> browse databases and collections
  -> inspect selected collection
  -> preview chunks
  -> chunk, embed, and store with /api/index/document
  -> search with retrieval controls
```

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8765/api/status"

Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8765/api/mongodb/databases"

Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8765/api/mongodb/collections?database=RAG_with_MongoDB"

Invoke-RestMethod -Method Get `
  -Uri "http://127.0.0.1:8765/api/mongodb/collection/summary?database=RAG_with_MongoDB&collection=profile_chunks"

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8765/api/document/chunks" `
  -ContentType "application/json" `
  -Body '{"title":"Smoke Document","source_id":"smoke-document","text":"This smoke document verifies chunk preview before embedding and storage."}'

# This is the full chunk, embed, and store endpoint.
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8765/api/index/document" `
  -ContentType "application/json" `
  -Body '{"title":"Smoke Document","source_id":"smoke-document","text":"This smoke document verifies chunk embedding, MongoDB storage, and vector search retrieval."}'

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8765/api/search" `
  -ContentType "application/json" `
  -Body '{"query":"What does the smoke document verify?","top_k":10,"min_score":0.6,"num_candidates":150,"exact":false,"source_id_filter":"smoke-document"}'
```

## Hosted API Calls

```powershell
$api = "https://YOUR-HOSTED-API.example.com"
Invoke-RestMethod -Method Get -Uri "$api/health"
Invoke-RestMethod -Method Post `
  -Uri "$api/ask" `
  -ContentType "application/json" `
  -Body '{"question":"What is this knowledge base about?","top_k":3}'
```
