from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()
assistants_db = {}

class AssistantCreate(BaseModel):
    name: str
    icon: Optional[str] = ""
    description: Optional[str] = ""
    prompt_content: Optional[str] = ""
    model_parameters: Optional[dict] = {}
    knowledge_ids: Optional[List[int]] = []

class AssistantUpdate(BaseModel):
    name: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    prompt_content: Optional[str]
    model_parameters: Optional[dict]
    knowledge_ids: Optional[List[int]]

@router.get("/admin/assistants")
def list_assistants():
    return {"success": True, "data": list(assistants_db.values())}

@router.post("/admin/assistants")
def create_assistant(data: AssistantCreate):
    new_id = len(assistants_db) + 1
    assistants_db[new_id] = data.dict()
    assistants_db[new_id]["id"] = new_id
    assistants_db[new_id]["update_time"] = datetime.now().isoformat()
    return {"success": True, "message": "助手创建成功"}

@router.put("/admin/assistants/{assistant_id}")
def update_assistant(assistant_id: int, data: AssistantUpdate):
    if assistant_id not in assistants_db:
        return {"success": False, "message": "助手不存在"}
    for k, v in data.dict(exclude_unset=True).items():
        assistants_db[assistant_id][k] = v
    assistants_db[assistant_id]["update_time"] = datetime.now().isoformat()
    return {"success": True, "message": "助手更新成功"}

@router.delete("/admin/assistants/{assistant_id}")
def delete_assistant(assistant_id: int):
    if assistant_id in assistants_db:
        del assistants_db[assistant_id]
        return {"success": True, "message": "助手删除成功"}
    return {"success": False, "message": "助手不存在"}

@router.put("/admin/assistants/{assistant_id}/prompt")
def update_prompt(assistant_id: int, prompt_content: str):
    if assistant_id not in assistants_db:
        return {"success": False, "message": "助手不存在"}
    assistants_db[assistant_id]["prompt_content"] = prompt_content
    assistants_db[assistant_id]["update_time"] = datetime.now().isoformat()
    return {"success": True, "message": "提示词更新成功"}

@router.put("/admin/assistants/{assistant_id}/parameters")
def update_parameters(assistant_id: int, model_parameters: dict):
    if assistant_id not in assistants_db:
        return {"success": False, "message": "助手不存在"}
    assistants_db[assistant_id]["model_parameters"] = model_parameters
    assistants_db[assistant_id]["update_time"] = datetime.now().isoformat()
    return {"success": True, "message": "参数更新成功"}

@router.put("/admin/assistants/{assistant_id}/knowledge_binding")
def bind_knowledge(assistant_id: int, knowledge_ids: List[int]):
    if assistant_id not in assistants_db:
        return {"success": False, "message": "助手不存在"}
    assistants_db[assistant_id]["knowledge_ids"] = knowledge_ids
    assistants_db[assistant_id]["update_time"] = datetime.now().isoformat()
    return {"success": True, "message": "知识库绑定成功"}
