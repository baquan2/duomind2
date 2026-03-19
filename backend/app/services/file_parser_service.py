from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, UploadFile, status

from app.utils.helpers import normalize_text


ALLOWED_EXTENSIONS = {".txt", ".md", ".docx"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
DOCX_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


async def extract_text_from_upload(file: UploadFile) -> tuple[str, str]:
    filename = file.filename or "tep-khong-ten"
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chi ho tro tep .txt, .md va .docx.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tep tai len dang rong.",
        )

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tep vuot qua gioi han 5MB.",
        )

    if extension in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore")
    elif extension == ".docx":
        text = _extract_docx_text(content)
    else:
        text = ""

    normalized = normalize_text(text)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Khong doc duoc noi dung tu tep nay.",
        )

    return text.strip(), filename


def _extract_docx_text(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            document_xml = archive.read("word/document.xml")
    except (BadZipFile, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tep .docx khong hop le.",
        ) from exc

    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []

    for paragraph in root.findall(".//w:body/w:p", DOCX_NAMESPACE):
        texts = [
            node.text.strip()
            for node in paragraph.findall(".//w:t", DOCX_NAMESPACE)
            if node.text and node.text.strip()
        ]
        if texts:
            paragraphs.append("".join(texts))

    return "\n".join(paragraphs)
