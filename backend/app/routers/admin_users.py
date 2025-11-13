from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_admin_user
from app.models.user import User
from app.utils.security import hash_password

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    role: str = "user"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class ResetPasswordBody(BaseModel):
    new_password: str


def serialize_user(user: User) -> dict:
    return {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "create_time": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/admin/users")
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    data = db.query(User).order_by(User.username).all()
    return {"success": True, "data": [serialize_user(item) for item in data]}


@router.post("/admin/users")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    payload.role = payload.role or "user"
    if db.get(User, payload.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if payload.role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="角色不合法")
    user = User(
        username=payload.username,
        password=hash_password(payload.password),
        email=payload.email,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    return {"success": True, "message": "创建成功", "data": serialize_user(user)}


@router.put("/admin/users/{username}")
def update_user(
    username: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    user = db.get(User, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if payload.role and payload.role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="角色不合法")
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    db.commit()
    db.refresh(user)
    return {"success": True, "message": "修改成功", "data": serialize_user(user)}


@router.delete("/admin/users/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    user = db.get(User, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"success": True, "message": "删除成功"}


@router.post("/admin/users/{username}/reset_password")
def reset_password(
    username: str,
    payload: ResetPasswordBody,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    user = db.get(User, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password = hash_password(payload.new_password)
    db.commit()
    return {"success": True, "message": "密码已重置"}
