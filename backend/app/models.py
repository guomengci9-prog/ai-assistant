from pydantic import BaseModel
from typing import Optional, List

# 用户模型
class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# 助手模型
class Assistant(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

# 聊天消息
class ChatMessage(BaseModel):
    role: str   # "user" 或 "assistant"
    content: str
