from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.sql import func

from app.core.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(String(64), primary_key=True, index=True)
    assistant_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "assistant_id": self.assistant_id,
            "title": self.title or "",
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else None,
        }


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    assistant_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, default="")
    message_type = Column(String(32), default="text")
    attachments = Column(SQLiteJSON, default=list)
    hide_name = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "assistant_id": self.assistant_id,
            "role": self.role,
            "content": self.content or "",
            "message_type": self.message_type or "text",
            "attachments": self.attachments or [],
            "hideName": bool(self.hide_name),
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
        }


class AttachmentChunk(Base):
    __tablename__ = "attachment_chunks"

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, nullable=False, index=True)
    conversation_id = Column(String(64), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, default="")
    embedding = Column(SQLiteJSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "assistant_id": self.assistant_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "chunk_index": self.chunk_index,
            "content": self.content or "",
            "embedding": self.embedding or [],
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else None,
        }
