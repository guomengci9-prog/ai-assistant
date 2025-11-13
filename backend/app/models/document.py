from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    content_type = Column(String(128), default="")
    assistant_id = Column(Integer, nullable=True)
    parse_status = Column(String(32), default="unparsed")
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    parameters = Column(SQLiteJSON, default=dict)
    parse_result = Column(SQLiteJSON, default=dict)
    description = Column(Text, default="")
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "assistant_id": self.assistant_id,
            "parse_status": self.parse_status,
            "parsed_at": (
                self.parsed_at.isoformat() if isinstance(self.parsed_at, datetime) else None
            ),
            "parameters": self.parameters or {},
            "parse_result": self.parse_result or {},
            "description": self.description or "",
            "upload_time": (
                self.upload_time.isoformat() if isinstance(self.upload_time, datetime) else None
            ),
            "update_time": (
                self.update_time.isoformat() if isinstance(self.update_time, datetime) else None
            ),
        }

    @property
    def absolute_path(self) -> Path:
        """Convenience path helper for storage operations."""
        return Path(self.file_path).resolve()


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    assistant_id = Column(Integer, nullable=True, index=True)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, default="")
    embedding = Column(SQLiteJSON, default=list)
    embedding_model = Column(String(64), default="")
    chunk_metadata = Column(SQLiteJSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "assistant_id": self.assistant_id,
            "chunk_index": self.chunk_index,
            "content": self.content or "",
            "embedding": self.embedding or [],
            "embedding_model": self.embedding_model or "",
            "metadata": self.chunk_metadata or {},
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None,
        }
