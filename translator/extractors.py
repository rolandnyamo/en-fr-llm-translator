import io
from pathlib import Path
from typing import Optional

import chardet


def read_txt(path: Path) -> str:
    data = path.read_bytes()
    det = chardet.detect(data)
    enc = det.get("encoding") or "utf-8"
    try:
        return data.decode(enc, errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def read_docx(path: Path) -> str:
    try:
        from docx import Document  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "python-docx is required to process .docx files. Install with `pip install python-docx`."
        ) from e

    doc = Document(str(path))
    parts = []
    for para in doc.paragraphs:
        parts.append(para.text)
    return "\n".join(parts)


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "pypdf is required to process .pdf files. Install with `pip install pypdf`."
        ) from e

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        # Extract text; note this may not preserve layout
        text = page.extract_text() or ""
        parts.append(text)
    return "\n\n".join(parts)


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return read_txt(path)
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    raise ValueError(f"Unsupported file type: {suffix}")

