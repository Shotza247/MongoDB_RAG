from __future__ import annotations

import json

from mongodb_vector_test_ui.retrieval.rerankers import create_reranker


def main() -> None:
    candidates = [
        {
            "chunk_id": "architecture",
            "source_id": "reranker-smoke-test",
            "score": 0.71,
            "text": "The Profile Agent stores vector embeddings in MongoDB Atlas.",
        },
        {
            "chunk_id": "unrelated",
            "source_id": "reranker-smoke-test",
            "score": 0.83,
            "text": "The portfolio supports a light and dark visual theme.",
        },
        {
            "chunk_id": "retrieval",
            "source_id": "reranker-smoke-test",
            "score": 0.68,
            "text": "MongoDB Vector Search retrieves candidate chunks for grounded answers.",
        },
    ]
    reranker = create_reranker()
    results = reranker.rerank(
        "Where does the Profile Agent store and retrieve its knowledge?",
        candidates,
    )
    evidence = [
        {
            "rerank_position": item.get("rerank_position"),
            "chunk_id": item.get("chunk_id"),
            "source_id": item.get("source_id"),
            "vector_score": item.get("vector_score"),
            "rerank_score": item.get("rerank_score"),
        }
        for item in results
    ]
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
