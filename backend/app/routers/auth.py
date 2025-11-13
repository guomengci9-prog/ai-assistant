from __future__ import annotations

import random
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Float, String, text
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine, get_db
from app.models.user import User
from app.utils.security import hash_password

router = APIRouter()


class VerificationCode(Base):
    __tablename__ = "verification_codes"
    account = Column(String, primary_key=True, index=True)
    code = Column(String)
    expire_time = Column(Float)


Base.metadata.create_all(bind=engine)


def ensure_user_columns() -> None:
    with engine.connect() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
        if "role" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'"))
        if "created_at" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN created_at TEXT"))
            conn.execute(text("UPDATE users SET created_at = datetime('now') WHERE created_at IS NULL"))


def ensure_default_admin() -> None:
    with SessionLocal() as db:
        exists = db.query(User).filter(User.role == "admin").first()
        if not exists:
            admin = User(
                username="admin",
                password=hash_password("admin123"),
                role="admin",
                email=None,
                phone=None,
            )
            db.add(admin)
            db.commit()


ensure_user_columns()
ensure_default_admin()


class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    account: str
    password: str


class ForgotPasswordRequest(BaseModel):
    account: str


class ResetPasswordRequest(BaseModel):
    account: str
    code: str
    new_password: str


def generate_code() -> str:
    return f"{random.randint(100000, 999999)}"


def find_user_by_account(db: Session, account: str) -> Optional[User]:
    return (
        db.query(User)
        .filter(
            (User.username == account)
            | (User.email == account)
            | (User.phone == account)
        )
        .first()
    )


@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    if find_user_by_account(db, user.username):
        return {"success": False, "message": "用户名已存在"}
    if user.email and db.query(User).filter(User.email == user.email).first():
        return {"success": False, "message": "邮箱已注册"}
    if user.phone and db.query(User).filter(User.phone == user.phone).first():
        return {"success": False, "message": "手机号已注册"}

    db_user = User(
        username=user.username,
        password=hash_password(user.password),
        email=user.email,
        phone=user.phone,
        role="user",
    )
    db.add(db_user)
    db.commit()
    return {"success": True, "message": "注册成功"}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = find_user_by_account(db, user.account)
    if not db_user:
        return {"success": False, "message": "用户不存在"}
    if db_user.password != hash_password(user.password):
        return {"success": False, "message": "密码错误"}
    token = f"token-{db_user.username}"
    return {
        "success": True,
        "message": "登录成功",
        "token": token,
        "role": db_user.role or "user",
    }


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    db_user = find_user_by_account(db, req.account)
    if not db_user:
        return {"success": False, "message": "账户不存在"}

    code = generate_code()
    expire_time = time.time() + 300

    db_code = (
        db.query(VerificationCode).filter(VerificationCode.account == req.account).first()
    )
    if db_code:
        db_code.code = code
        db_code.expire_time = expire_time
    else:
        db_code = VerificationCode(account=req.account, code=code, expire_time=expire_time)
        db.add(db_code)

    db.commit()
    print(f"验证码发送到 {req.account}: {code} (有效5分钟)")
    return {"success": True, "message": "验证码已发送"}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    db_code = (
        db.query(VerificationCode).filter(VerificationCode.account == req.account).first()
    )
    if not db_code:
        return {"success": False, "message": "请先获取验证码"}
    if req.code != db_code.code:
        return {"success": False, "message": "验证码错误"}
    if time.time() > db_code.expire_time:
        db.delete(db_code)
        db.commit()
        return {"success": False, "message": "验证码已过期"}

    db_user = find_user_by_account(db, req.account)
    if not db_user:
        db.delete(db_code)
        db.commit()
        return {"success": False, "message": "用户不存在"}

    db_user.password = hash_password(req.new_password)
    db.delete(db_code)
    db.commit()
    return {"success": True, "message": "密码已重置"}
