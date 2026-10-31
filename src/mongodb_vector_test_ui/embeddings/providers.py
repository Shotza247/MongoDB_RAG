import hashlib
import math
import random

import requests

from mongodb_vector_test_ui.core.config import Settings


def embed_documents(texts: list[str], settings: Settings) -> list[list[float]]:
    provider = settings.embedding_provider.lower()
    if provider == "hashing":
        return [_hash_embedding(text, settings.vector_dimensions) for text in texts]
    if provider == "voyage":
        return _voyage_embed(texts, settings, input_type="document")
    if provider == "openai":
        return _openai_embed(texts, settings)
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={settings.embedding_provider!r}")


def embed_query(text: str, settings: Settings) -> list[float]:
    provider = settings.embedding_provider.lower()
    if provider == "hashing":
        return _hash_embedding(text, settings.vector_dimensions)
    if provider == "voyage":
        return _voyage_embed([text], settings, input_type="query")[0]
    if provider == "openai":
        return _openai_embed(text, settings)[0]
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={settings.embedding_provider!r}")


def _voyage_embed(texts: list[str], settings: Settings, input_type: str) -> list[list[float]]:
    if not settings.voyage_api_key:
        raise ValueError("VOYAGE_API_KEY is required for Voyage embeddings.")

    if settings.voyage_model.startswith("voyage-context"):
        body = {
            "inputs": [texts] if input_type == "document" else texts,
            "model": settings.voyage_model,
            "input_type": input_type,
            "output_dimension": settings.vector_dimensions,
        }
        url = f"{settings.voyage_base_url}/contextualizedembeddings"
    else:
        body = {
            "input": texts,
            "model": settings.voyage_model,
            "input_type": input_type,
            "output_dimension": settings.vector_dimensions,
        }
        url = f"{settings.voyage_base_url}/embeddings"

    return _extract_embeddings(_post_json(url, settings.voyage_api_key, body))


def _openai_embed(input_value: str | list[str], settings: Settings) -> list[list[float]]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings.")
    body = {
        "model": settings.openai_embedding_model,
        "input": input_value,
        "dimensions": settings.vector_dimensions,
    }
    return _extract_embeddings(_post_json("https://api.openai.com/v1/embeddings", settings.openai_api_key, body))


def _post_json(url: str, api_key: str, body: dict) -> dict:
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=body,
        timeout=90,
    )
    if not response.ok:
        raise RuntimeError(f"Embedding request failed: {response.status_code} {response.text}")
    return response.json()


def _hash_embedding(text: str, dimensions: int) -> list[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    vector = [rng.uniform(-1.0, 1.0) for _ in range(dimensions)]
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _extract_embeddings(payload: dict) -> list[list[float]]:
    embeddings = _collect_embeddings(payload.get("data", payload))
    if not embeddings:
        raise RuntimeError(f"Embedding response did not include embeddings. Keys: {sorted(payload)}")
    return embeddings


def _collect_embeddings(value: object) -> list[list[float]]:
    embeddings: list[list[float]] = []
    if isinstance(value, dict):
        maybe = value.get("embedding")
        if isinstance(maybe, list) and maybe and all(isinstance(x, int | float) for x in maybe):
            embeddings.append(maybe)
        for child in value.values():
            if child is not maybe:
                embeddings.extend(_collect_embeddings(child))
    elif isinstance(value, list):
        for child in value:
            embeddings.extend(_collect_embeddings(child))
    return embeddings
