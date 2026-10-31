import pytest

from mongodb_vector_test_ui.core.config import Settings, with_mongodb_target


def test_with_mongodb_target_allows_selected_database_and_collection() -> None:
    settings = with_mongodb_target(
        Settings(mongodb_db="default_db", mongodb_collection="default_collection"),
        database="rag_lab",
        collection="career_chunks",
    )

    assert settings.mongodb_db == "rag_lab"
    assert settings.mongodb_collection == "career_chunks"


def test_with_mongodb_target_rejects_invalid_database_name() -> None:
    with pytest.raises(ValueError, match="database name cannot contain"):
        with_mongodb_target(Settings(), database="bad.database", collection="chunks")


def test_with_mongodb_target_rejects_system_collection_target() -> None:
    with pytest.raises(ValueError, match="System collections"):
        with_mongodb_target(Settings(), database="rag_lab", collection="system.views")
