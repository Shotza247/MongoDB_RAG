import hashlib
import re


def chunk_text(source_id: str, title: str, text: str, max_chars: int = 1000) -> list[dict]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    chunks: list[dict] = []
    current = ""

    for paragraph in paragraphs or [text.strip()]:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(_make_chunk(source_id, title, current, len(chunks)))
        current = paragraph

    if current:
        chunks.append(_make_chunk(source_id, title, current, len(chunks)))
    return chunks


def _make_chunk(source_id: str, title: str, text: str, index: int) -> dict:
    chunk_id = hashlib.sha256(f"{source_id}:{index}:{text[:120]}".encode()).hexdigest()[:24]
    return {
        "chunk_id": chunk_id,
        "source_id": source_id,
        "text": text,
        "metadata": {"title": title, "chunk_index": index, "source_id": source_id},
    }
