from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import requests

from mongodb_vector_test_ui.core.config import Settings, get_settings

Candidate = Mapping[str, Any]
PostJson = Callable[..., Any]


class Reranker(Protocol):
    def rerank(
        self,
        query: str,
        candidates: Sequence[Candidate],
        *,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class VoyageRerankerConfig:
    api_key: str
    base_url: str = "https://ai.mongodb.com/v1"
    model: str = "rerank-2.5"
    timeout: int = 90


class VoyageReranker:
    """Rerank provider-neutral candidate records while preserving their metadata."""

    def __init__(
        self,
        config: VoyageRerankerConfig,
        *,
        post: PostJson = requests.post,
    ) -> None:
        self.config = config
        self._post = post

    def rerank(
        self,
        query: str,
        candidates: Sequence[Candidate],
        *,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Rerank query is required.")
        if not candidates:
            return []
        if not self.config.api_key:
            raise ValueError("VOYAGE_API_KEY is required for Voyage reranking.")
        if top_k is not None and not 1 <= top_k <= len(candidates):
            raise ValueError("Rerank top_k must be between 1 and the candidate count.")

        documents = []
        for index, candidate in enumerate(candidates):
            text = str(candidate.get("text", "")).strip()
            if not text:
                raise ValueError(f"Rerank candidate {index} has no text.")
            documents.append(text)

        body: dict[str, Any] = {
            "query": clean_query,
            "documents": documents,
            "model": self.config.model,
            "top_k": top_k,
            "return_documents": False,
            "truncation": True,
        }

        response = self._post(
            f"{self.config.base_url.rstrip('/')}/rerank",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=self.config.timeout,
        )
        if not response.ok:
            raise RuntimeError(f"Voyage reranking request failed with HTTP {response.status_code}.")
        return _merge_rerank_results(candidates, response.json())


def create_reranker(
    provider: str | None = None,
    *,
    settings: Settings | None = None,
    post: PostJson = requests.post,
) -> Reranker:
    current = settings or get_settings()
    selected = (provider or os.getenv("RERANK_PROVIDER", "voyage")).strip().lower()
    if selected == "none":
        return IdentityReranker()
    if selected == "voyage":
        return VoyageReranker(
            VoyageRerankerConfig(
                api_key=current.voyage_api_key,
                base_url=current.voyage_base_url,
                model=os.getenv("VOYAGE_RERANK_MODEL", "rerank-2.5").strip(),
                timeout=_int_env("RERANK_TIMEOUT_SECONDS", 90),
            ),
            post=post,
        )
    raise ValueError(f"Unsupported RERANK_PROVIDER={selected!r}.")


def safe_reranker_diagnostics(settings: Settings | None = None) -> dict[str, Any]:
    current = settings or get_settings()
    provider = os.getenv("RERANK_PROVIDER", "voyage").strip().lower()
    return {
        "rerank_provider": provider,
        "rerank_model": os.getenv("VOYAGE_RERANK_MODEL", "rerank-2.5").strip(),
        "rerank_api_key_set": bool(current.voyage_api_key) if provider == "voyage" else None,
        "rerank_base_url": current.voyage_base_url if provider == "voyage" else None,
        "rerank_timeout_seconds": _int_env("RERANK_TIMEOUT_SECONDS", 90),
    }


class IdentityReranker:
    def rerank(
        self,
        query: str,
        candidates: Sequence[Candidate],
        *,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        del query
        limit = len(candidates) if top_k is None else top_k
        return [dict(candidate) for candidate in candidates[:limit]]


def _merge_rerank_results(
    candidates: Sequence[Candidate],
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise TypeError("Voyage reranking response did not include a data list.")

    merged = []
    seen_indexes: set[int] = set()
    for item in data:
        if not isinstance(item, Mapping):
            raise TypeError("Voyage reranking response contained an invalid result.")
        index = item.get("index")
        score = item.get("relevance_score")
        if not isinstance(index, int) or not 0 <= index < len(candidates):
            raise RuntimeError("Voyage reranking response contained an invalid candidate index.")
        if index in seen_indexes:
            raise RuntimeError("Voyage reranking response contained a duplicate candidate index.")
        if not isinstance(score, int | float):
            raise TypeError("Voyage reranking response contained an invalid relevance score.")
        seen_indexes.add(index)
        candidate = dict(candidates[index])
        candidate["vector_score"] = candidate.get("vector_score", candidate.get("score"))
        candidate["rerank_score"] = float(score)
        candidate["rerank_position"] = len(merged) + 1
        merged.append(candidate)
    return merged


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value else default
