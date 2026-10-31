import pytest

from mongodb_vector_test_ui.core.config import Settings
from mongodb_vector_test_ui.retrieval.rerankers import (
    IdentityReranker,
    VoyageReranker,
    VoyageRerankerConfig,
    create_reranker,
)


class FakeResponse:
    ok = True
    status_code = 200

    def json(self):
        return {
            "data": [
                {"index": 1, "relevance_score": 0.91},
                {"index": 0, "relevance_score": 0.72},
            ]
        }


def test_voyage_reranker_preserves_metadata_and_vector_score():
    request = {}

    def fake_post(url, **kwargs):
        request.update(url=url, **kwargs)
        return FakeResponse()

    reranker = VoyageReranker(
        VoyageRerankerConfig(api_key="test-key"),
        post=fake_post,
    )
    candidates = [
        {"text": "first", "score": 0.81, "chunk_id": "a"},
        {
            "text": "second",
            "score": 0.73,
            "chunk_id": "b",
            "source_id": "profile",
            "title": "Career Profile",
            "section": "Architecture",
        },
    ]

    results = reranker.rerank("Which is relevant?", candidates)

    assert [item["chunk_id"] for item in results] == ["b", "a"]
    assert results[0]["vector_score"] == 0.73
    assert results[0]["rerank_score"] == 0.91
    assert results[0]["rerank_position"] == 1
    assert results[0]["source_id"] == "profile"
    assert results[0]["title"] == "Career Profile"
    assert results[0]["section"] == "Architecture"
    assert results[0]["text"] == "second"
    assert request["url"] == "https://ai.mongodb.com/v1/rerank"
    assert request["json"]["documents"] == ["first", "second"]
    assert request["json"]["top_k"] is None
    assert request["json"]["return_documents"] is False
    assert "test-key" not in str(request["json"])


def test_voyage_reranker_sends_optional_top_k():
    request = {}

    def fake_post(url, **kwargs):
        request.update(url=url, **kwargs)
        return FakeResponse()

    reranker = VoyageReranker(VoyageRerankerConfig(api_key="test-key"), post=fake_post)
    reranker.rerank(
        "query",
        [{"text": "first"}, {"text": "second"}],
        top_k=2,
    )
    assert request["json"]["top_k"] == 2


def test_empty_candidates_skip_provider_request():
    reranker = VoyageReranker(VoyageRerankerConfig(api_key=""))
    assert reranker.rerank("query", []) == []


def test_candidate_text_is_required():
    reranker = VoyageReranker(VoyageRerankerConfig(api_key="test-key"))
    with pytest.raises(ValueError, match="candidate 0"):
        reranker.rerank("query", [{"chunk_id": "missing-text"}])


def test_identity_reranker_is_provider_neutral():
    candidates = [{"text": "a"}, {"text": "b"}]
    assert IdentityReranker().rerank("query", candidates, top_k=1) == [{"text": "a"}]


def test_factory_uses_existing_voyage_settings():
    settings = Settings(
        voyage_api_key="test-key",
        voyage_base_url="https://ai.mongodb.com/v1",
    )
    assert isinstance(create_reranker(settings=settings), VoyageReranker)
