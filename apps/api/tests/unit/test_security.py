"""Test password hashing, JWT, Fernet encryption."""

from __future__ import annotations

import pytest

from phongthuy_bds.core.security import (
    TokenError,
    create_access_token,
    decode_token,
    decrypt_pii,
    encrypt_pii,
    hash_password,
    verify_password,
)


class TestPassword:
    def test_hash_verify(self) -> None:
        h = hash_password("supersecret")
        assert h != "supersecret"
        assert verify_password("supersecret", h)
        assert not verify_password("wrong", h)


class TestJwt:
    def test_round_trip(self) -> None:
        token = create_access_token(
            sub="user-1", tenant_id="tenant-1", role="broker",
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-1"
        assert payload["tenant_id"] == "tenant-1"
        assert payload["role"] == "broker"
        assert payload["type"] == "access"

    def test_tampered_token_rejected(self) -> None:
        token = create_access_token("u", "t", "broker")
        with pytest.raises(TokenError):
            decode_token(token + "tampered")


class TestPii:
    def test_round_trip(self) -> None:
        plain = "Nguyễn Văn A"
        ciphertext = encrypt_pii(plain)
        assert ciphertext != plain.encode("utf-8")
        assert decrypt_pii(ciphertext) == plain

    def test_unicode_preserved(self) -> None:
        ciphertext = encrypt_pii("Đào Thị Hằng — 0901234567")
        assert decrypt_pii(ciphertext) == "Đào Thị Hằng — 0901234567"
