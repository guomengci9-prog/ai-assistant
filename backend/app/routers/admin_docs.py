from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()
docs_db = {}

class DocUpdate(BaseModel):
    name: Optional[str]
    parameters: Optional[dict]
    assistant_id: Optional[int]

@router.get("/admin/docs")
def list_docs():
    return {"success": True, "data": list(docs_db.values())}

@router.post("/admin/docs")
def upload_doc(file: UploadFile = File(...)):
    doc_id = len(docs_db) + 1
    docs_db[doc_id] = {
        "id": doc_id,
        "name": file.filename,
        "file_path": f"./uploads/{file.filename}",
        "assistant_id": None,
        "parse_status": "未解析",
        "parameters": {},
        "upload_time": datetime.now().isoformat()
    }
    # 可以在这里保存文件
    return {"success": True, "message": "上传成功", "data": docs_db[doc_id]}

@router.post("/admin/docs/{doc_id}/parse")
def parse_doc(doc_id: int):
    if doc_id not in docs_db:
        return {"success": False, "message": "文档不存在"}
    docs_db[doc_id]["parse_status"] = "已解析"
    return {"success": True, "message": "解析完成"}

@router.put("/admin/docs/{doc_id}")
def update_doc(doc_id: int, data: DocUpdate):
    if doc_id not in docs_db:
        return {"success": False, "message": "文档不存在"}
    for k, v in data.dict(exclude_unset=True).items():
        docs_db[doc_id][k] = v
    return {"success": True, "message": "文档更新成功"}

@router.delete("/admin/docs/{doc_id}")
def delete_doc(doc_id: int):
    if doc_id in docs_db:
        del docs_db[doc_id]
        return {"success": True, "message": "删除成功"}
    return {"success": False, "message": "文档不存在"}
