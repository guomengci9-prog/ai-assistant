import json
from typing import Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_admin_user
from app.services import documents as document_service

router = APIRouter()


class DocUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict] = None
    assistant_id: Optional[int] = None
    parse_status: Optional[str] = Field(default=None, pattern=r"^[\w\-]+$")


@router.get("/admin/docs")
def list_docs(
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    data = document_service.list_documents(db)
    return {"success": True, "data": data}


@router.post("/admin/docs")
async def upload_doc(
    file: UploadFile = File(...),
    assistant_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    parameters: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    extra_params: Dict = {}
    if parameters:
        try:
            extra_params = json.loads(parameters)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="parameters 字段需为 JSON 字符串")

    created = document_service.create_document(
        db,
        upload_file=file,
        assistant_id=assistant_id,
        description=description or "",
        parameters=extra_params,
    )
    return {"success": True, "message": "上传成功", "data": created}


@router.post("/admin/docs/{doc_id}/parse")
def parse_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    parsed = document_service.parse_document(db, doc_id)
    if not parsed:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "message": "解析完成", "data": parsed}


@router.put("/admin/docs/{doc_id}")
def update_doc(
    doc_id: int,
    data: DocUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    payload = data.dict(exclude_unset=True)
    if not payload:
        doc = document_service.get_document(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"success": True, "message": "无变更", "data": doc.to_dict()}

    updated = document_service.update_document(db, doc_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "message": "文档更新成功", "data": updated}


@router.delete("/admin/docs/{doc_id}")
def delete_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    admin_user=Depends(get_admin_user),
):
    deleted = document_service.delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "message": "删除成功"}
