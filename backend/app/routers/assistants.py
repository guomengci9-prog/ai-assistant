from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import assistants as assistant_service

router = APIRouter()


class Assistant(BaseModel):
    id: int
    name: str
    icon: str
    description: str
    prompt_content: Optional[str] = None
    system_prompt: Optional[str] = None
    scene_prompt: Optional[str] = None
    user_prefill: Optional[str] = None
    opening_message: Optional[str] = None
    default_prompt: Optional[str] = Field(default=None, alias="defaultPrompt")
    model_parameters: Dict[str, Any] = Field(default_factory=dict)
    knowledge_ids: List[int] = Field(default_factory=list)
    update_time: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


def _normalize_assistant(raw: Dict[str, Any]) -> Dict[str, Any]:
    """补充 defaultPrompt 字段"""
    result = dict(raw)
    result.setdefault("prompt_content", "")
    result.setdefault("system_prompt", "")
    result.setdefault("scene_prompt", "")
    result.setdefault("user_prefill", "")
    result.setdefault("opening_message", "")
    result.setdefault("model_parameters", {})
    result.setdefault("knowledge_ids", [])
    if "defaultPrompt" not in result:
        result["defaultPrompt"] = result.get("prompt_content", "")
    return result


@router.get("/assistants", response_model=List[Assistant])
def get_assistants(db: Session = Depends(get_db)):
    assistant_service.seed_assistants(db)
    data = assistant_service.list_assistants(db)
    return [_normalize_assistant(item) for item in data]


@router.get("/assistants/{assistant_id}", response_model=Assistant)
def get_assistant_by_id(assistant_id: int, db: Session = Depends(get_db)):
    assistant_service.seed_assistants(db)
    assistant = assistant_service.get_assistant(db, assistant_id)
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return _normalize_assistant(assistant)
