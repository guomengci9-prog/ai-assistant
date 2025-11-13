from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.models.assistant import Assistant

Base.metadata.create_all(bind=engine)

SEED_ASSISTANTS: Iterable[Dict[str, str]] = [
    {
        "name": "文档助手",
        "icon": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
        "description": "帮你解读 PDF、操作手册和技术文档内容",
        "prompt_content": "请以结构化方式解读文档，并给出重点摘要与可执行建议。",
        "system_prompt": "你是一名专业的技术顾问，擅长阅读和解构多种文档格式。",
        "scene_prompt": "当前场景：用户需要理解技术文档或说明书中的关键信息。",
        "user_prefill": "我现在遇到了下面的文档问题：",
        "opening_message": "你好，我是文档助手，告诉我你正在阅读的文档或遇到的困惑吧。",
    },
    {
        "name": "翻译助手",
        "icon": "https://cdn-icons-png.flaticon.com/512/6073/6073873.png",
        "description": "支持中英互译，保持语气自然。",
        "prompt_content": "请把用户的内容进行准确、自然的中英翻译。",
        "system_prompt": "你是一名专业的翻译员，熟悉多领域术语。",
        "scene_prompt": "当前场景：提供高质量的双语翻译服务。",
        "user_prefill": "请翻译以下内容：",
        "opening_message": "你好，我是翻译助手，直接输入要翻译的内容就可以了。",
    },
    {
        "name": "科研问答助手",
        "icon": "https://cdn-icons-png.flaticon.com/512/9018/9018883.png",
        "description": "面向学术研究与论文答疑。",
        "prompt_content": "回答时给出严谨的推理过程和引用建议。",
        "system_prompt": "你是一名科研助手，熟悉论文阅读、实验设计与数据解读。",
        "scene_prompt": "当前场景：为科研工作者提供学术问答支持。",
        "user_prefill": "我的科研问题是：",
        "opening_message": "你好，我是科研助手，可以告诉我你的研究主题或遇到的问题。",
    },
]


def seed_assistants(db: Session) -> None:
    if db.scalar(select(Assistant).limit(1)):
        return
    for payload in SEED_ASSISTANTS:
        assistant = Assistant(**payload)
        db.add(assistant)
    db.commit()


def list_assistants(db: Session) -> List[Dict]:
    result = db.scalars(select(Assistant).order_by(Assistant.id)).all()
    return [item.to_dict() for item in result]


def get_assistant(db: Session, assistant_id: int) -> Optional[Dict]:
    assistant = db.get(Assistant, assistant_id)
    return assistant.to_dict() if assistant else None


def create_assistant(db: Session, payload: Dict) -> Dict:
    assistant = Assistant(**payload)
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return assistant.to_dict()


def update_assistant(db: Session, assistant_id: int, payload: Dict) -> Optional[Dict]:
    assistant = db.get(Assistant, assistant_id)
    if not assistant:
        return None
    for key, value in payload.items():
        setattr(assistant, key, value)
    assistant.update_time = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant)
    return assistant.to_dict()


def delete_assistant(db: Session, assistant_id: int) -> Optional[Dict]:
    assistant = db.get(Assistant, assistant_id)
    if not assistant:
        return None
    db.delete(assistant)
    db.commit()
    return assistant.to_dict()
