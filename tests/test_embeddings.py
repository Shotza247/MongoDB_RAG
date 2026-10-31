from mongodb_vector_test_ui.core.config import Settings
from mongodb_vector_test_ui.embeddings.providers import embed_query


def test_hashing_embedding_is_available_without_api_keys() -> None:
    settings = Settings(embedding_provider="hashing", vector_dimensions=8)

    vector = embed_query("mongodb vector search", settings)

    assert len(vector) == 8
    assert abs(sum(value * value for value in vector) - 1.0) < 0.000001
