from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceSelection:
    evidence: tuple[dict[str, Any], ...]
    candidate_count: int
    minimum_requested: int
    maximum_requested: int

    @property
    def minimum_met(self) -> bool:
        return len(self.evidence) >= self.minimum_requested


def select_evidence(
    candidates: Sequence[Mapping[str, Any]],
    *,
    minimum: int = 3,
    maximum: int = 5,
) -> EvidenceSelection:
    """Select top unique chunks by rerank score and preserve citation metadata."""
    if not 1 <= minimum <= maximum <= 20:
        raise ValueError("Evidence selection requires 1 <= minimum <= maximum <= 20.")

    unique: dict[tuple[str, str], tuple[int, dict[str, Any]]] = {}
    for position, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise TypeError(f"Evidence candidate {position} must be an object.")
        text = str(candidate.get("text") or "").strip()
        source_id = str(candidate.get("source_id") or "").strip()
        chunk_id = str(candidate.get("chunk_id") or "").strip()
        if not text:
            raise ValueError(f"Evidence candidate {position} has no text.")
        if not source_id or not chunk_id:
            raise ValueError(f"Evidence candidate {position} must include source_id and chunk_id.")
        score_value = candidate.get("rerank_score")
        if score_value is None:
            score_value = candidate.get("vector_score", candidate.get("score"))
        try:
            score = float(score_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Evidence candidate {position} has no valid rerank_score or vector score."
            ) from exc
        if not math.isfinite(score):
            raise ValueError(f"Evidence candidate {position} has a non-finite rerank_score.")

        key = (source_id, chunk_id)
        if key not in unique:
            item = dict(candidate)
            item.update(source_id=source_id, chunk_id=chunk_id, text=text)
            item.setdefault("rerank_score", score if candidate.get("rerank_score") is not None else None)
            item["_selection_score"] = score
            unique[key] = (position, item)

    ordered = sorted(unique.values(), key=lambda item: (-item[1]["_selection_score"], item[0]))
    evidence = []
    for _, item in ordered[:maximum]:
        item.pop("_selection_score", None)
        evidence.append(item)
    return EvidenceSelection(
        evidence=tuple(evidence),
        candidate_count=len(candidates),
        minimum_requested=minimum,
        maximum_requested=maximum,
    )
