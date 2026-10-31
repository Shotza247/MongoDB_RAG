import io
import zipfile

from mongodb_vector_test_ui.ingestion.documents import extract_from_bytes


def test_extract_text_document_normalizes_content() -> None:
    document = extract_from_bytes(
        b"Profile Agent\r\n\r\nMongoDB vector search pipeline with Voyage embeddings.",
        filename="profile.txt",
    )

    assert document.title == "profile"
    assert document.source_id == "profile"
    assert "MongoDB vector search" in document.text
    assert "\r" not in document.text


def test_extract_docx_document_reads_paragraph_text() -> None:
    docx_bytes = _minimal_docx(
        "<w:p><w:r><w:t>Profile Agent</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>DOCX extraction for chunking and embeddings.</w:t></w:r></w:p>"
    )

    document = extract_from_bytes(docx_bytes, filename="profile-agent.docx")

    assert document.extension == ".docx"
    assert document.source_id == "profile-agent"
    assert "DOCX extraction" in document.text


def _minimal_docx(body_xml: str) -> bytes:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body_xml}</w:body>"
        "</w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()
