from __future__ import annotations

import io
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree

MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".log", ".html", ".htm"}
SUPPORTED_EXTENSIONS = sorted([*TEXT_EXTENSIONS, ".docx", ".pdf"])
WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@dataclass(frozen=True)
class ExtractedDocument:
    filename: str
    extension: str
    title: str
    source_id: str
    characters: int
    text: str
    source_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def extract_from_path(file_path: str) -> ExtractedDocument:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise ValueError("File path does not exist.")
    if not path.is_file():
        raise ValueError("File path must point to a document file.")
    data = path.read_bytes()
    return extract_from_bytes(data, filename=path.name, source_path=str(path))


def extract_from_bytes(data: bytes, filename: str, source_path: str = "") -> ExtractedDocument:
    filename = Path(filename or "uploaded-document").name
    extension = Path(filename).suffix.lower()
    if not data:
        raise ValueError("Document is empty.")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document is larger than the 12 MB test UI limit.")

    if extension in TEXT_EXTENSIONS or not extension:
        text = _decode_text(data)
    elif extension == ".docx":
        text = _extract_docx(data)
    elif extension == ".pdf":
        text = _extract_pdf(data)
    else:
        supported = ", ".join(SUPPORTED_EXTENSIONS)
        raise ValueError(f"Unsupported document type '{extension}'. Supported types: {supported}.")

    text = _normalize_text(text)
    if len(text) < 20:
        raise ValueError("Extracted text is too short to chunk. Check the source document.")

    title = Path(filename).stem or "Document"
    return ExtractedDocument(
        filename=filename,
        extension=extension or ".txt",
        title=title,
        source_id=_slug(title),
        characters=len(text),
        text=text,
        source_path=source_path,
    )


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _extract_docx(data: bytes) -> str:
    paragraphs: list[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml_names = [
                name
                for name in archive.namelist()
                if name == "word/document.xml" or name.startswith(("word/header", "word/footer"))
            ]
            for name in xml_names:
                paragraphs.extend(_extract_docx_xml(archive.read(name)))
    except zipfile.BadZipFile as exc:
        raise ValueError("DOCX file is not a valid zipped Word document.") from exc

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _extract_docx_xml(xml_bytes: bytes) -> list[str]:
    root = ElementTree.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NAMESPACE}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{WORD_NAMESPACE}tab":
                parts.append("\t")
            elif node.tag == f"{WORD_NAMESPACE}br":
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ValueError("PDF extraction requires pypdf. Run python -m pip install -e .") from exc

    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(page for page in pages if page)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    return "-".join(part for part in "".join(chars).split("-") if part)[:80] or "document"
