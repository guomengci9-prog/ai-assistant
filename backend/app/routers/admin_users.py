from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hashlib

router = APIRouter()
users_db = {}  # 模拟数据库

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"

class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    role: Optional[str]

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

@router.get("/admin/users")
def list_users():
    return {"success": True, "data": list(users_db.values())}

@router.post("/admin/users")
def create_user(user: UserCreate):
    if user.username in users_db:
        return {"success": False, "message": "用户名已存在"}
    users_db[user.username] = {
        "id": len(users_db) + 1,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "password": hash_password(user.password),
        "create_time": datetime.now().isoformat()
    }
    return {"success": True, "message": "创建成功"}

@router.put("/admin/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    for u in users_db.values():
        if u["id"] == user_id:
            if user.username: u["username"] = user.username
            if user.email: u["email"] = user.email
            if user.role: u["role"] = user.role
            return {"success": True, "message": "修改成功"}
    return {"success": False, "message": "用户不存在"}

@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int):
    for k, u in list(users_db.items()):
        if u["id"] == user_id:
            del users_db[k]
            return {"success": True, "message": "删除成功"}
    return {"success": False, "message": "用户不存在"}

@router.post("/admin/users/{user_id}/reset_password")
def reset_password(user_id: int, new_password: str = "123456"):
    for u in users_db.values():
        if u["id"] == user_id:
            u["password"] = hash_password(new_password)
            return {"success": True, "message": "密码已重置"}
    return {"success": False, "message": "用户不存在"}
