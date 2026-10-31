# Hosted API Checklist

Use this when local ingestion works but the deployed API fails.

The reusable template's required production API target is FastAPI on Vercel. The
Starlette implementation is retained only as the verified MVP1 reference contract.

## Required Deployment Settings

- Start command:

```text
python -m uvicorn profile_agent.api:app --host 0.0.0.0 --port $PORT --http h11
```

- Required environment variables:

```text
MONGODB_URI
MONGODB_DB
MONGODB_COLLECTION
VECTOR_INDEX_NAME
VECTOR_FIELD
VECTOR_DIMENSIONS
EMBEDDING_PROVIDER
VOYAGE_BASE_URL
VOYAGE_API_KEY
VOYAGE_MODEL
ALLOWED_ORIGINS
```

## Checks

1. Confirm the host uses the project virtual environment or installs from `pyproject.toml`.
2. Confirm the host has all environment variables set.
3. Confirm `VOYAGE_BASE_URL` matches the key type.
4. Confirm MongoDB Atlas Network Access allows the hosting provider.
5. Confirm the app binds to `0.0.0.0`, not `127.0.0.1`.
6. Confirm the app uses the hosting provider's `$PORT`.
7. Confirm CORS includes the portfolio domain.
8. Confirm `/health` works before testing `/ask`.
9. Confirm `/ask` works with a short question.
10. Confirm logs do not print secrets.

## Common Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| App works locally but not hosted | Bound to `127.0.0.1` | Use `--host 0.0.0.0` |
| Host reports no open port | Ignoring `$PORT` | Use provider port variable |
| Mongo timeout | Atlas network access missing | Add host IP range or provider egress |
| Voyage 403 | Wrong base URL for key type | Use `https://ai.mongodb.com/v1` for Atlas Model API keys |
| Browser CORS error | Portfolio origin not allowed | Update `ALLOWED_ORIGINS` |
| Pydantic DLL blocked on Windows | Native dependency policy | Recreate the environment in an approved location, request an administrator allow rule, or use WSL2/Docker; do not bypass policy |

## Hosted Smoke Test

```powershell
$api = "https://YOUR-HOSTED-API.example.com"
Invoke-RestMethod -Method Get -Uri "$api/health"
Invoke-RestMethod -Method Post `
  -Uri "$api/ask" `
  -ContentType "application/json" `
  -Body '{"question":"What are the strongest project examples?","top_k":3}'
```

Record the result in `PIPELINE_AUDIT.md`.
