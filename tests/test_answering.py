import pytest

from mongodb_vector_test_ui.core.config import Settings
from mongodb_vector_test_ui.llm import answering
from mongodb_vector_test_ui.llm.grounding import GroundedAnswer


class FakeReranker:
    def rerank(self, question, candidates, top_k=None):
        return [
            {**candidate, "rerank_score": 1.0 - index / 10}
            for index, candidate in enumerate(candidates)
        ]


class FakeStructuredChatModel:
    def __init__(self, response):
        self.response = response

    def with_structured_output(self, schema):
        assert schema is GroundedAnswer
        return self

    def invoke(self, messages):
        assert len(messages) == 2
        return self.response


class FakeAdapter:
    def __init__(self, response):
        self.model = FakeStructuredChatModel(response)

    def create_chat_model(self, config):
        return self.model


@pytest.mark.parametrize("response_type", ["mapping", "pydantic"])
def test_answer_workflow_uses_structured_output_and_resolves_citations(
    monkeypatch, response_type
):
    payload = {
        "answer": "The profile connects these areas [E1][E2][E3].",
        "citation_ids": ["E1", "E2", "E3"],
        "insufficient_evidence": False,
    }
    response = payload if response_type == "mapping" else GroundedAnswer(**payload)
    adapter = FakeAdapter(response)
    monkeypatch.setattr(answering, "create_reranker", lambda settings: FakeReranker())
    candidates = [
        {
            "source_id": "profile",
            "chunk_id": f"chunk-{index}",
            "text": f"Evidence chunk {index}",
            "score": 0.9 - index / 10,
        }
        for index in range(3)
    ]

    result = answering.synthesize_answer(
        "Connect the profile evidence.",
        candidates,
        settings=Settings(),
        adapter=adapter,
    )

    assert result["answer"] == payload["answer"]
    assert result["evidence_count"] == 3
    assert [citation["evidence_id"] for citation in result["citations"]] == [
        "E1",
        "E2",
        "E3",
    ]
    assert all(citation["chunk_id"].startswith("chunk-") for citation in result["citations"])
