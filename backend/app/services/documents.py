from __future__ import annotations

import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.models.document import Document, DocumentChunk
from app.utils.embedding import DEFAULT_VECTOR_DIM, chunk_text, compute_embedding

try:  # Optional dependency for richer parsing
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads" / "docs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOC_CHUNK_CHAR_LIMIT = 800
DOC_CHUNK_OVERLAP = 120
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".log"}
DEFAULT_EMBEDDING_MODEL = "builtin-hash"


def _resolve_parameters(document: Document) -> Dict:
    params = document.parameters if isinstance(document.parameters, dict) else {}
    chunk_size = params.get("chunk_size") or params.get("chunk", {}).get("size")
    chunk_overlap = params.get("chunk_overlap") or params.get("chunk", {}).get("overlap")
    embedding_cfg = params.get("embedding") or {}
    metadata_cfg = params.get("metadata") if isinstance(params.get("metadata"), dict) else {}
    toc_level = params.get("toc_level")

    def _safe_int(value, default):
        try:
            ivalue = int(value)
            return ivalue if ivalue > 0 else default
        except Exception:
            return default

    resolved = {
        "chunk_size": _safe_int(chunk_size, DOC_CHUNK_CHAR_LIMIT),
        "chunk_overlap": _safe_int(chunk_overlap, DOC_CHUNK_OVERLAP),
        "embedding_model": embedding_cfg.get("model") or DEFAULT_EMBEDDING_MODEL,
        "embedding_dimension": _safe_int(
            embedding_cfg.get("dimension"), DEFAULT_VECTOR_DIM
        ),
        "toc_level": _safe_int(toc_level, None) if toc_level not in (None, "") else None,
        "metadata": metadata_cfg,
    }
    max_contexts = params.get("top_k") or params.get("retrieve_top_k")
    if max_contexts:
        resolved["top_k"] = _safe_int(max_contexts, 0)
    similarity = params.get("similarity_threshold")
    if isinstance(similarity, (int, float)):
        resolved["similarity_threshold"] = float(similarity)
    return resolved


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _read_pdf(path: Path) -> str:
    if not PdfReader:
        return ""
    try:
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except Exception:
        return ""


def _extract_text(path: Path, content_type: str | None) -> str:
    content_type = (content_type or "").lower()
    suffix = path.suffix.lower()
    if content_type.startswith("text/") or suffix in TEXT_SUFFIXES:
        return _read_text_file(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    return ""


HEADING_MD = re.compile(r"^(#{1,6})\s+(.+)")
HEADING_NUMERIC = re.compile(r"^(\d+(?:\.\d+){0,5})\s+(.+)")


def _detect_heading(line: str) -> Optional[Tuple[int, str]]:
    line = line.strip()
    if not line:
        return None
    md = HEADING_MD.match(line)
    if md:
        return len(md.group(1)), md.group(2).strip()
    num = HEADING_NUMERIC.match(line)
    if num:
        level = min(len(num.group(1).split(".")), 6)
        return level, num.group(2).strip()
    return None


def _split_sections(text: str, max_level: Optional[int]) -> List[Dict[str, str | int]]:
    lines = text.splitlines()
    sections: List[Dict[str, str | int]] = []
    current = {"title": "", "level": 1, "content": []}  # type: ignore

    for line in lines:
        detected = _detect_heading(line)
        if detected:
            level, title = detected
            if max_level is None or level <= max_level:
                if current["content"]:
                    sections.append(
                        {
                            "title": current["title"],
                            "level": current["level"],
                            "content": "\n".join(current["content"]),
                        }
                    )
                current = {"title": title, "level": level, "content": []}  # type: ignore
                continue
        current["content"].append(line)

    if current["content"]:
        sections.append(
            {
                "title": current["title"],
                "level": current["level"],
                "content": "\n".join(current["content"]),
            }
        )
    return [section for section in sections if section.get("content", "").strip()]


def _make_storage_path(original_filename: str) -> Path:
    suffix = Path(original_filename or "").suffix or ".bin"
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{suffix}"
    return UPLOAD_DIR / unique_name


def _relative_path(absolute_path: Path) -> str:
    try:
        return absolute_path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return absolute_path.as_posix()


def list_documents(db: Session) -> List[Dict]:
    docs = db.scalars(select(Document).order_by(Document.id.desc())).all()
    return [doc.to_dict() for doc in docs]


def get_document(db: Session, doc_id: int) -> Optional[Document]:
    return db.get(Document, doc_id)


def create_document(
    db: Session,
    *,
    upload_file,
    assistant_id: Optional[int] = None,
    description: str = "",
    parameters: Optional[Dict] = None,
) -> Dict:
    storage_path = _make_storage_path(upload_file.filename)
    with storage_path.open("wb") as destination:
        shutil.copyfileobj(upload_file.file, destination)

    relative_path = _relative_path(storage_path)
    file_size = storage_path.stat().st_size
    document = Document(
        name=Path(upload_file.filename).stem or "Untitled Document",
        original_filename=upload_file.filename,
        file_path=relative_path,
        file_size=file_size,
        content_type=getattr(upload_file, "content_type", "") or "",
        assistant_id=assistant_id,
        description=description or "",
        parameters=parameters or {},
        parse_status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document.to_dict()


def update_document(db: Session, doc_id: int, payload: Dict) -> Optional[Dict]:
    doc = db.get(Document, doc_id)
    if not doc:
        return None
    for key, value in payload.items():
        if hasattr(doc, key):
            setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc.to_dict()


def parse_document(db: Session, doc_id: int) -> Optional[Dict]:
    doc = db.get(Document, doc_id)
    if not doc:
        return None

    stored_path = Path(doc.file_path)
    absolute_path = stored_path if stored_path.is_absolute() else (BASE_DIR / stored_path)
    exists = absolute_path.exists()
    parse_summary = {
        "file_exists": exists,
        "file_size": doc.file_size,
        "chunk_count": 0,
    }

    if not exists:
        doc.parse_status = "missing_file"
        parse_summary["message"] = "File missing, status updated"
    else:
        extracted_text = _extract_text(absolute_path, doc.content_type)
        params = _resolve_parameters(doc)
        section_entries = _split_sections(extracted_text, params.get("toc_level"))
        if not section_entries:
            section_entries = [
                {"title": doc.name or "", "level": 1, "content": extracted_text}
            ]

        parse_summary["char_count"] = len(extracted_text)
        parse_summary["sections"] = len(section_entries)
        parse_summary["parameters_applied"] = params

        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

        chunk_counter = 0
        base_metadata = params.get("metadata") or {}
        for section_index, section in enumerate(section_entries):
            section_content = section.get("content", "")
            section_title = section.get("title") or ""
            section_level = section.get("level") or 1
            section_chunks = chunk_text(
                section_content,
                params["chunk_size"],
                params["chunk_overlap"],
            )

            for local_index, chunk_text_value in enumerate(section_chunks):
                embedding = compute_embedding(
                    chunk_text_value, vector_dim=params["embedding_dimension"]
                )
                metadata = {
                    "section_title": section_title,
                    "section_level": section_level,
                    "section_index": section_index,
                    "chunk_in_section": local_index,
                    "document_title": doc.name,
                    "vector_dim": params["embedding_dimension"],
                    **base_metadata,
                }
                db.add(
                    DocumentChunk(
                        document_id=doc.id,
                        assistant_id=doc.assistant_id,
                        chunk_index=chunk_counter,
                        content=chunk_text_value,
                        embedding=embedding,
                        embedding_model=params["embedding_model"],
                        chunk_metadata=metadata,
                    )
                )
                chunk_counter += 1

        parse_summary["chunk_count"] = chunk_counter
        doc.parse_status = "parsed" if chunk_counter else "parsed_no_text"

    doc.parsed_at = datetime.now(timezone.utc)
    doc.parse_result = parse_summary
    db.commit()
    db.refresh(doc)
    return doc.to_dict()


def delete_document(db: Session, doc_id: int) -> bool:
    doc = db.get(Document, doc_id)
    if not doc:
        return False

    stored_path = Path(doc.file_path)
    absolute_path = stored_path if stored_path.is_absolute() else (BASE_DIR / stored_path)
    if absolute_path.exists():
        try:
            absolute_path.unlink()
        except OSError:
            pass
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

    db.delete(doc)
    db.commit()
    return True
