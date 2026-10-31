from mongodb_vector_test_ui.chunking.service import chunk_text


def test_chunk_text_creates_stable_chunks() -> None:
    text = "Experience\n\nBuilt a MongoDB vector search test UI.\n\nProjects\n\nCreated RAG tooling."

    chunks = chunk_text("profile", "Profile", text, max_chars=50)

    assert len(chunks) >= 2
    assert chunks[0]["source_id"] == "profile"
    assert chunks[0]["metadata"]["title"] == "Profile"
    assert chunks[0]["chunk_id"] == chunk_text("profile", "Profile", text, max_chars=50)[0][
        "chunk_id"
    ]
