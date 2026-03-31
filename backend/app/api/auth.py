"""
Authentication API - 注册、登录、Token 管理
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


# ========== Request/Response Schemas ==========

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    username: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: str

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=512)


# ========== Helpers ==========

def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ========== Endpoints ==========

@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户，返回 JWT token"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    # 创建用户
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        username=req.username or req.email.split("@")[0],
        phone=req.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成 token
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=user_to_dict(user))


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """邮箱密码登录，返回 JWT token"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=user_to_dict(user))


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(**user_to_dict(current_user))


@router.put("/me", response_model=UserResponse, summary="更新个人信息")
async def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.username is not None:
        current_user.username = req.username
    if req.phone is not None:
        current_user.phone = req.phone
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url

    await db.commit()
    await db.refresh(current_user)
    return UserResponse(**user_to_dict(current_user))


@router.post("/change-password", summary="修改密码")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )

    current_user.hashed_password = hash_password(req.new_password)
    await db.commit()
    return {"message": "密码修改成功"}


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """用当前有效 token 换取新 token"""
    token = create_access_token({"sub": current_user.id})
    return TokenResponse(access_token=token, user=user_to_dict(current_user))
