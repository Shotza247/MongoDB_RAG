from mongodb_vector_test_ui.core.config import Settings
from mongodb_vector_test_ui.vectorstore.mongodb import (
    FILTER_FIELDS,
    MongoVectorStore,
    build_vector_search_pipeline,
)


def test_desired_vector_index_definition_includes_filter_fields() -> None:
    store = MongoVectorStore.__new__(MongoVectorStore)
    store.settings = Settings()

    definition = store.desired_vector_index_definition()
    filter_paths = [
        field["path"] for field in definition["fields"] if field.get("type") == "filter"
    ]

    assert filter_paths == list(FILTER_FIELDS)


def test_vector_search_pipeline_applies_min_score_and_candidates() -> None:
    settings = Settings(vector_num_candidates=150)

    pipeline = build_vector_search_pipeline(
        settings,
        query_embedding=[0.1, 0.2],
        top_k=5,
        min_score=0.6,
        num_candidates=120,
    )

    assert pipeline[0]["$vectorSearch"]["limit"] == 5
    assert pipeline[0]["$vectorSearch"]["numCandidates"] == 120
    assert pipeline[2] == {"$match": {"score": {"$gte": 0.6}}}


def test_vector_search_pipeline_omits_candidates_for_exact_search() -> None:
    pipeline = build_vector_search_pipeline(
        Settings(),
        query_embedding=[0.1, 0.2],
        top_k=3,
        exact=True,
    )

    vector_stage = pipeline[0]["$vectorSearch"]
    assert vector_stage["exact"] is True
    assert "numCandidates" not in vector_stage


def test_vector_search_pipeline_adds_supported_filters() -> None:
    pipeline = build_vector_search_pipeline(
        Settings(),
        query_embedding=[0.1, 0.2],
        top_k=3,
        filters={
            "metadata.source_id": "document-ingestion-smoke-test",
            "metadata.title": "Profile Agent Test Document",
            "metadata.section": "Projects",
            "chunk_id": "abc123,def456",
        },
    )

    assert pipeline[0]["$vectorSearch"]["filter"] == {
        "$and": [
            {"metadata.source_id": "document-ingestion-smoke-test"},
            {"metadata.title": "Profile Agent Test Document"},
            {"metadata.section": "Projects"},
            {"chunk_id": {"$in": ["abc123", "def456"]}},
        ]
    }
