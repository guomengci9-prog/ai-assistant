from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.sql import func

from app.core.database import Base


class Assistant(Base):
    __tablename__ = "assistants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    icon = Column(String(255), nullable=True)
    description = Column(Text, default="")
    prompt_content = Column(Text, default="")
    system_prompt = Column(Text, default="")
    scene_prompt = Column(Text, default="")
    user_prefill = Column(Text, default="")
    opening_message = Column(Text, default="")
    model_parameters = Column(SQLiteJSON, default=dict)
    knowledge_ids = Column(SQLiteJSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon or "",
            "description": self.description or "",
            "prompt_content": self.prompt_content or "",
            "system_prompt": self.system_prompt or "",
            "scene_prompt": self.scene_prompt or "",
            "user_prefill": self.user_prefill or "",
            "opening_message": self.opening_message or "",
            "model_parameters": self.model_parameters or {},
            "knowledge_ids": self.knowledge_ids or [],
            "defaultPrompt": (self.prompt_content or ""),
            "update_time": (
                self.update_time.isoformat()
                if isinstance(self.update_time, datetime)
                else None
            ),
        }
