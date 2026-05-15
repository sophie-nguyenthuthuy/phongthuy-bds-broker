"""Integration: health + readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/v1/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ready(client: TestClient) -> None:
    r = client.get("/v1/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["checks"]["db"] == "ok"


def test_root(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Phong Thủy BĐS API" in r.text
