"""Integration: register → login → /me round-trip."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAuthFlow:
    def test_register_returns_token(self, client: TestClient) -> None:
        r = client.post(
            "/v1/auth/register",
            json={
                "tenant_name": "Sàn Test",
                "full_name": "Trần Test",
                "email": "test@example.com",
                "password": "abcdefgh123",
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"

    def test_login_after_register(self, client: TestClient) -> None:
        client.post(
            "/v1/auth/register",
            json={
                "tenant_name": "Sàn A",
                "full_name": "User A",
                "email": "a@example.com",
                "password": "abcdefgh123",
            },
        )
        r = client.post(
            "/v1/auth/login",
            json={"email": "a@example.com", "password": "abcdefgh123"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["access_token"]

    def test_wrong_password_rejected(self, client: TestClient) -> None:
        client.post(
            "/v1/auth/register",
            json={
                "tenant_name": "Sàn B",
                "full_name": "User B",
                "email": "b@example.com",
                "password": "abcdefgh123",
            },
        )
        r = client.post(
            "/v1/auth/login",
            json={"email": "b@example.com", "password": "wrongwrongwrong"},
        )
        assert r.status_code == 401

    def test_me_endpoint(self, client: TestClient) -> None:
        reg = client.post(
            "/v1/auth/register",
            json={
                "tenant_name": "Sàn C",
                "full_name": "User C",
                "email": "c@example.com",
                "password": "abcdefgh123",
            },
        ).json()
        r = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {reg['access_token']}"},
        )
        assert r.status_code == 200
        assert r.json()["email"] == "c@example.com"
        assert r.json()["role"] == "owner"

    def test_me_without_token_unauthorized(self, client: TestClient) -> None:
        r = client.get("/v1/auth/me")
        assert r.status_code == 401

    def test_duplicate_email_rejected(self, client: TestClient) -> None:
        body = {
            "tenant_name": "Sàn D",
            "full_name": "User D",
            "email": "d@example.com",
            "password": "abcdefgh123",
        }
        client.post("/v1/auth/register", json=body)
        r = client.post("/v1/auth/register", json=body)
        assert r.status_code == 409
