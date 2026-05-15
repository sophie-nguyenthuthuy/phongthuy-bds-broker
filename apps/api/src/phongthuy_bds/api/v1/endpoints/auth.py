"""Auth endpoints — login, register tenant + owner user, refresh."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from phongthuy_bds.api.deps import CurrentUser, DbDep
from phongthuy_bds.core.config import get_settings
from phongthuy_bds.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from phongthuy_bds.db.models import Tenant, User, UserRole
from phongthuy_bds.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký sàn môi giới mới + tài khoản chủ",
)
def register(req: RegisterRequest, db: DbDep) -> TokenResponse:
    existing = db.execute(
        select(User).where(User.email == req.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã đăng ký",
        )

    tenant = Tenant(name=req.tenant_name)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        phone=req.phone,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=UserRole.OWNER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(
            sub=str(user.id), tenant_id=str(tenant.id), role=user.role.value,
        ),
        refresh_token=create_refresh_token(
            sub=str(user.id), tenant_id=str(tenant.id),
        ),
        expires_in_min=get_settings().jwt_access_ttl_min,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: DbDep) -> TokenResponse:
    user = db.execute(
        select(User).where(User.email == req.email)
    ).scalar_one_or_none()
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai email hoặc mật khẩu",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản bị khóa",
        )

    user.last_login_at = datetime.now(UTC)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(
            sub=str(user.id), tenant_id=str(user.tenant_id), role=user.role.value,
        ),
        refresh_token=create_refresh_token(
            sub=str(user.id), tenant_id=str(user.tenant_id),
        ),
        expires_in_min=get_settings().jwt_access_ttl_min,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str, db: DbDep) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Refresh không hợp lệ: {e}",
        ) from e
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Phải là refresh token",
        )
    user_id = payload["sub"]
    import uuid as _uuid
    user = db.get(User, _uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không hoạt động",
        )
    return TokenResponse(
        access_token=create_access_token(
            sub=str(user.id), tenant_id=str(user.tenant_id), role=user.role.value,
        ),
        refresh_token=create_refresh_token(
            sub=str(user.id), tenant_id=str(user.tenant_id),
        ),
        expires_in_min=get_settings().jwt_access_ttl_min,
    )


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
