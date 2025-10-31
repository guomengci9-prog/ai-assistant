# app/routers/assistants.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

assistants_db = [
    {
        "id": 1,
        "name": "文档助手",
        "icon": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
        "description": "帮你解读 PDF、手册与文档内容",
        "defaultPrompt": "我是一个专业的文档分析助手，擅长解析 PDF、手册和技术文档。",
        "update_time": datetime.now().isoformat(),
    },
    {
        "id": 2,
        "name": "翻译助手",
        "icon": "https://cdn-icons-png.flaticon.com/512/6073/6073873.png",
        "description": "支持中英双向智能翻译",
        "defaultPrompt": "我是专业的翻译助手，回答准确自然，请输入你的问题吧。",
        "update_time": datetime.now().isoformat(),
    },
    {
        "id": 3,
        "name": "科研问答助手",
        "icon": "https://cdn-icons-png.flaticon.com/512/9018/9018883.png",
        "description": "适用于学术论文、科研答疑",
        "defaultPrompt": "我是一个是科研专家，擅长学术研究与论文解释。",
        "update_time": datetime.now().isoformat(),
    },
]


# -------------------------------
# 数据模型
# -------------------------------
class Assistant(BaseModel):
    id: int
    name: str
    icon: str
    description: str
    defaultPrompt: Optional[str] = None 
    update_time: Optional[str] = None

# -------------------------------
# 获取助手列表
# -------------------------------
@router.get("/assistants", response_model=List[Assistant])
def get_assistants():
    return assistants_db

# -------------------------------
# 根据ID获取助手详情
# -------------------------------
@router.get("/assistants/{assistant_id}", response_model=Assistant)
def get_assistant_by_id(assistant_id: int):
    for a in assistants_db:
        if a["id"] == assistant_id:
            return a
    return {"detail": "Assistant not found"}
