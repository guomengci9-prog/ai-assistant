from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib
import random
import time

router = APIRouter()

# ------------------ 数据库 ------------------
DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 用户表
class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, unique=True, nullable=True)

# 验证码表
class VerificationCode(Base):
    __tablename__ = "verification_codes"
    account = Column(String, primary_key=True, index=True)
    code = Column(String)
    expire_time = Column(Float)

Base.metadata.create_all(bind=engine)

# ------------------ 数据模型 ------------------
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

# ------------------ 工具函数 ------------------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_code():
    return f"{random.randint(100000, 999999)}"

def find_user_by_account(db, account: str):
    return db.query(User).filter(
        (User.username == account) |
        (User.email == account) |
        (User.phone == account)
    ).first()

# ------------------ 注册接口 ------------------
@router.post("/register")
def register(user: UserRegister):
    db = SessionLocal()
    if find_user_by_account(db, user.username):
        db.close()
        return {"success": False, "message": "用户名已存在"}
    if user.email and db.query(User).filter(User.email == user.email).first():
        db.close()
        return {"success": False, "message": "邮箱已注册"}
    if user.phone and db.query(User).filter(User.phone == user.phone).first():
        db.close()
        return {"success": False, "message": "手机号已注册"}

    db_user = User(
        username=user.username,
        password=hash_password(user.password),
        email=user.email,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.close()
    print("POST /register 被调用")
    return {"success": True, "message": "注册成功"}

# ------------------ 登录接口 ------------------
@router.post("/login")
def login(user: UserLogin):
    db = SessionLocal()
    db_user = find_user_by_account(db, user.account)
    if not db_user:
        db.close()
        return {"success": False, "message": "用户不存在"}
    if db_user.password != hash_password(user.password):
        db.close()
        return {"success": False, "message": "密码错误"}
    db.close()
    return {"success": True, "message": "登录成功", "token": f"token-{db_user.username}"}

# ------------------ 忘记密码接口 ------------------
@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    db = SessionLocal()
    db_user = find_user_by_account(db, req.account)
    if not db_user:
        db.close()
        return {"success": False, "message": "账户不存在"}

    code = generate_code()
    expire_time = time.time() + 300  # 5分钟有效

    # 保存或更新验证码
    db_code = db.query(VerificationCode).filter(VerificationCode.account == req.account).first()
    if db_code:
        db_code.code = code
        db_code.expire_time = expire_time
    else:
        db_code = VerificationCode(account=req.account, code=code, expire_time=expire_time)
        db.add(db_code)

    db.commit()
    db.close()
    print(f"验证码发送到 {req.account}: {code} (有效期5分钟)")
    return {"success": True, "message": "验证码已发送"}

# ------------------ 重置密码接口 ------------------
@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    db = SessionLocal()
    db_code = db.query(VerificationCode).filter(VerificationCode.account == req.account).first()
    if not db_code:
        db.close()
        return {"success": False, "message": "请先获取验证码"}
    if req.code != db_code.code:
        db.close()
        return {"success": False, "message": "验证码错误"}
    if time.time() > db_code.expire_time:
        db.delete(db_code)
        db.commit()
        db.close()
        return {"success": False, "message": "验证码已过期"}

    db_user = find_user_by_account(db, req.account)
    if not db_user:
        db.delete(db_code)
        db.commit()
        db.close()
        return {"success": False, "message": "用户不存在"}

    db_user.password = hash_password(req.new_password)
    db.delete(db_code)  # 删除验证码
    db.commit()
    db.close()
    return {"success": True, "message": "密码已重置成功"}
