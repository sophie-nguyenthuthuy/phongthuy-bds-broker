"""Mật mã: JWT + password hash + Fernet encryption cho DLCN."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from phongthuy_bds.core.config import get_settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Password ────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ─── JWT ─────────────────────────────────────────────────────────
class TokenError(Exception):
    pass


def create_access_token(
    sub: str,
    tenant_id: str,
    role: str,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_min)).timestamp()),
        "type": "access",
        **(extra or {}),
    }
    return jwt.encode(
        payload,
        settings.api_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(sub: str, tenant_id: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_refresh_ttl_days)).timestamp()),
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        settings.api_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.api_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        raise TokenError(str(e)) from e


# ─── DLCN encryption (NĐ 13/2023/NĐ-CP) ──────────────────────────
def _fernet() -> Fernet:
    """Encrypt sổ đỏ + ngày sinh khi lưu trữ.

    Theo NĐ 13/2023/NĐ-CP Điều 21: dữ liệu cá nhân nhạy cảm phải được mã hóa
    khi lưu trữ. Khóa nằm trong env, không commit code.
    """
    settings = get_settings()
    key = settings.dlcn_encryption_key.get_secret_value().encode()
    return Fernet(key)


def encrypt_pii(plain: str) -> bytes:
    return _fernet().encrypt(plain.encode("utf-8"))


def decrypt_pii(token: bytes) -> str:
    try:
        return _fernet().decrypt(token).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Không giải mã được dữ liệu — sai khóa hoặc dữ liệu hỏng") from e
