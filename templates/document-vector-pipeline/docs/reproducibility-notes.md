# Reproducibility Notes

## What Must Be Reproducible

- Environment setup
- Document loading
- Chunk counts
- Embedding provider and model
- Vector dimensions
- MongoDB database/collection/index names
- API health check
- First retrieval response
- Deployment start command
- Deployment environment variables

## What Should Not Be Committed

- `.env`
- API keys
- MongoDB connection strings
- Raw private documents
- Synced Box/Drive files
- `.venv/`
- `__pycache__/`
- local logs with secrets

## Recommended GitHub Shape

```text
src/
scripts/
tests/
docs/
templates/
data/
  source_documents/.gitkeep
.env.example
.gitignore
README.md
pyproject.toml
```

## Versioning Rule

When changing any of these, update the audit:

- embedding model
- vector dimension
- chunk size or overlap
- MongoDB index name
- document parser
- API route contract
- hosted start command
- CORS origins

## Minimum Done Definition

A project is ready to publish when:

- `python -m pytest -q` passes, or the audit explains why plugin autoload must be disabled.
- Ingestion works with one sample document.
- `/health` returns OK locally.
- `/ask` returns source-backed results locally.
- `.env` and raw private documents are ignored by Git.
- README includes exact setup and smoke-test commands.
