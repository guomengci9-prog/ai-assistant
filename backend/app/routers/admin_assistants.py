from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_admin_user
from app.services import assistants as assistant_service

router = APIRouter()


class AssistantBase(BaseModel):
    name: str
    icon: Optional[str] = ""
    description: Optional[str] = ""
    prompt_content: Optional[str] = ""
    system_prompt: Optional[str] = ""
    scene_prompt: Optional[str] = ""
    user_prefill: Optional[str] = ""
    opening_message: Optional[str] = ""
    model_parameters: Dict = Field(default_factory=dict)
    knowledge_ids: List[int] = Field(default_factory=list)


class AssistantCreate(AssistantBase):
    pass


class AssistantUpdate(BaseModel):
    name: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    prompt_content: Optional[str]
    system_prompt: Optional[str]
    scene_prompt: Optional[str]
    user_prefill: Optional[str]
    opening_message: Optional[str]
    model_parameters: Optional[Dict]
    knowledge_ids: Optional[List[int]]


class PromptUpdate(BaseModel):
    prompt_content: Optional[str] = None
    system_prompt: Optional[str] = None
    scene_prompt: Optional[str] = None
    user_prefill: Optional[str] = None
    opening_message: Optional[str] = None


@router.get("/admin/assistants")
def admin_list_assistants(
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    assistant_service.seed_assistants(db)
    data = assistant_service.list_assistants(db)
    return {"success": True, "data": data}


@router.post("/admin/assistants")
def create_assistant(
    data: AssistantCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    assistant_service.seed_assistants(db)
    created = assistant_service.create_assistant(db, data.dict())
    return {"success": True, "message": "Assistant created", "data": created}


@router.put("/admin/assistants/{assistant_id}")
def update_assistant(
    assistant_id: int,
    data: AssistantUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    payload = data.dict(exclude_unset=True)
    updated = assistant_service.update_assistant(db, assistant_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"success": True, "message": "Assistant updated", "data": updated}


@router.delete("/admin/assistants/{assistant_id}")
def delete_assistant(
    assistant_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    deleted = assistant_service.delete_assistant(db, assistant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"success": True, "message": "Assistant deleted", "data": deleted}


@router.put("/admin/assistants/{assistant_id}/prompt")
def update_prompt(
    assistant_id: int,
    data: PromptUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    payload = {k: (v if v is not None else "") for k, v in data.dict(exclude_unset=True).items()}
    if not payload:
        return {"success": True, "message": "No changes", "data": assistant_service.get_assistant(db, assistant_id)}
    updated = assistant_service.update_assistant(db, assistant_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"success": True, "message": "Prompts updated", "data": updated}


@router.put("/admin/assistants/{assistant_id}/parameters")
def update_parameters(
    assistant_id: int,
    model_parameters: Dict,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    updated = assistant_service.update_assistant(
        db, assistant_id, {"model_parameters": model_parameters or {}}
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"success": True, "message": "Parameters updated", "data": updated}


@router.put("/admin/assistants/{assistant_id}/knowledge_binding")
def bind_knowledge(
    assistant_id: int,
    knowledge_ids: List[int],
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    updated = assistant_service.update_assistant(
        db, assistant_id, {"knowledge_ids": knowledge_ids or []}
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"success": True, "message": "Knowledge binding updated", "data": updated}
