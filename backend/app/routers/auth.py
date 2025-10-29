from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import hashlib

router = APIRouter()

# 模拟数据库
users_db = {}

class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register")
def register(user: User):
    if user.username in users_db:
        return {"success": False, "message": "用户名已存在"}
    users_db[user.username] = {
        "password": hash_password(user.password),
        "email": user.email
    }
    return {"success": True, "message": "注册成功"}

@router.post("/login")
def login(user: User):
    if user.username not in users_db:
        return {"success": False, "message": "用户不存在"}
    if users_db[user.username]["password"] != hash_password(user.password):
        return {"success": False, "message": "密码错误"}
    return {"success": True, "message": "登录成功", "token": f"token-{user.username}"}
