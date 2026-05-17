"""End-to-end: register → customer → OCR sổ đỏ → chốt hướng → report → PDF.

Đây là test quan trọng nhất — bất kỳ regression nào trong engine/billing/generator
sẽ break ở đây.

PDF render được patch (weasyprint cần system libs Cairo/Pango không có ở CI test
job; được validate riêng ở Docker build job).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def _stub_pdf_render(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace weasyprint với stub — không kiểm tra rendering ở đây."""
    monkeypatch.setattr(
        "phongthuy_bds.services.report.generator.render_pdf_bytes",
        lambda html, base_url=None: b"%PDF-1.4 STUB\n",
    )


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient, email: str = "broker@e2e.example.com") -> tuple[str, str]:
    """Returns (access_token, tenant_id)."""
    r = client.post(
        "/v1/auth/register",
        json={
            "tenant_name": "Sàn Test E2E",
            "full_name": "Trần Test",
            "email": email,
            "password": "abcdefgh123",
        },
    )
    assert r.status_code == 201, r.text
    me = client.get("/v1/auth/me", headers=_auth_header(r.json()["access_token"]))
    return r.json()["access_token"], me.json()["tenant_id"]


def _grant_credit(db: Session, tenant_id: str, amount: int = 10) -> None:
    """Bỏ qua VNPay flow — nạp credit thẳng vào DB cho test."""
    import uuid as _uuid

    from phongthuy_bds.db.models import Tenant

    tenant = db.get(Tenant, _uuid.UUID(tenant_id))
    assert tenant is not None
    tenant.credit_balance = Decimal(amount)
    db.commit()


class TestFullReportFlow:
    def test_happy_path_male_1990_kham(
        self, client: TestClient, db: Session,
    ) -> None:
        # 1) Register + grant credit
        token, tenant_id = _register(client)
        _grant_credit(db, tenant_id, 5)

        # 2) Customer
        r = client.post(
            "/v1/customers",
            headers=_auth_header(token),
            json={
                "full_name": "Nguyễn Văn Khách",
                "phone": "0901234567",
                "birth_date": "1990-08-15",
                "gender": "nam",
                "consent_given": True,
            },
        )
        assert r.status_code == 201, r.text
        customer_id = r.json()["id"]
        assert r.json()["full_name"] == "Nguyễn Văn Khách"  # PII decrypted on return

        # 3) Upload sổ đỏ (OCR backend = mock returns canned data)
        r = client.post(
            "/v1/ocr/sodo",
            headers=_auth_header(token),
            files={"file": ("so-do.pdf", b"%PDF fake bytes", "application/pdf")},
        )
        assert r.status_code == 201, r.text
        land_title_id = r.json()["land_title_id"]
        assert r.json()["extracted"]["dia_chi"]  # mock returns this

        # 4) Cannot create report without house direction
        r = client.post(
            "/v1/reports",
            headers=_auth_header(token),
            json={
                "customer_id": customer_id,
                "land_title_id": land_title_id,
                "purposes": ["nhap_trach"],
            },
        )
        assert r.status_code == 400, r.text
        assert "hướng nhà" in r.json()["detail"].lower()

        # 5) Chốt hướng
        r = client.patch(
            f"/v1/ocr/sodo/{land_title_id}/direction",
            headers=_auth_header(token),
            json={"house_direction": "Đông Nam"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["land_title_id"] == land_title_id

        # 6) Tạo báo cáo
        r = client.post(
            "/v1/reports",
            headers=_auth_header(token),
            json={
                "customer_id": customer_id,
                "land_title_id": land_title_id,
                "purposes": ["nhap_trach", "dong_tho"],
                "good_day_window_start": "2026-06-01",
                "good_day_window_end": "2026-08-31",
                "good_day_top_k": 3,
            },
        )
        assert r.status_code == 201, r.text
        report = r.json()
        assert report["status"] == "ready"
        assert report["pdf_url"]

        # ─── Validate phong thủy output ───────────────────────────
        data = report["result_data"]
        assert data["cung_menh"]["cung"] == "Khảm"  # 1990 nam → Khảm
        assert data["cung_menh"]["nhom"] == "Đông tứ mệnh"
        assert data["cung_menh"]["can_chi"] == "Canh Ngọ"
        assert len(data["bat_trach"]) == 8

        # Đông Nam phải là Sinh Khí cho cung Khảm
        assert data["house_match"]["matched_quality"] == "Sinh Khí"
        assert data["house_match"]["is_good"]

        # 2 purpose phải có ngày tốt
        assert set(data["good_days"].keys()) == {"nhap_trach", "dong_tho"}
        for days in data["good_days"].values():
            for d in days:
                assert d["is_recommended"]
                assert d["score"] > 0
                # Không được có ngày chi Tý (xung tuổi Ngọ)
                assert "Tý" not in d["can_chi_day"].split()[1]

        # 7) Credit đã bị trừ
        r = client.get("/v1/billing/balance", headers=_auth_header(token))
        assert r.status_code == 200
        assert Decimal(r.json()["credit_balance"]) == Decimal("4")  # 5 - 1

        # 8) Download PDF
        report_id = report["id"]
        r = client.get(
            f"/v1/reports/{report_id}/pdf",
            headers=_auth_header(token),
        )
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content.startswith(b"%PDF")

    def test_insufficient_credit_returns_402(
        self, client: TestClient, db: Session,
    ) -> None:
        token, _ = _register(client, email="poor@e2e.example.com")
        # Không nạp credit. Setup KH + sổ đỏ.
        cust = client.post(
            "/v1/customers",
            headers=_auth_header(token),
            json={
                "full_name": "Khách Nghèo",
                "birth_date": "1985-01-01",
                "gender": "nu",
                "consent_given": True,
            },
        ).json()
        lt = client.post(
            "/v1/ocr/sodo",
            headers=_auth_header(token),
            files={"file": ("x.jpg", b"\xff\xd8\xff", "image/jpeg")},
        ).json()
        client.patch(
            f"/v1/ocr/sodo/{lt['land_title_id']}/direction",
            headers=_auth_header(token),
            json={"house_direction": "Bắc"},
        )
        r = client.post(
            "/v1/reports",
            headers=_auth_header(token),
            json={
                "customer_id": cust["id"],
                "land_title_id": lt["land_title_id"],
                "purposes": ["nhap_trach"],
            },
        )
        assert r.status_code == 402, r.text
        assert "tín dụng" in r.json()["detail"].lower()

    def test_consent_required(self, client: TestClient) -> None:
        token, _ = _register(client, email="noconsent@e2e.example.com")
        r = client.post(
            "/v1/customers",
            headers=_auth_header(token),
            json={
                "full_name": "Khách Không Đồng Thuận",
                "birth_date": "1990-01-01",
                "gender": "nam",
                "consent_given": False,
            },
        )
        assert r.status_code == 400
        assert "đồng thuận" in r.json()["detail"].lower() or "consent" in r.json()["detail"].lower()

    def test_cross_tenant_isolation(
        self, client: TestClient, db: Session,
    ) -> None:
        """Sàn A không được xem KH của sàn B."""
        token_a, _ = _register(client, email="a@e2e.example.com")
        token_b, _ = _register(client, email="b@e2e.example.com")

        cust_a = client.post(
            "/v1/customers",
            headers=_auth_header(token_a),
            json={
                "full_name": "KH của A",
                "birth_date": "1990-01-01",
                "gender": "nam",
                "consent_given": True,
            },
        ).json()

        # Sàn B cố xem KH của A → 404
        r = client.get(
            f"/v1/customers/{cust_a['id']}",
            headers=_auth_header(token_b),
        )
        assert r.status_code == 404

        # Sàn B list customers chỉ thấy của chính mình (rỗng)
        r = client.get("/v1/customers", headers=_auth_header(token_b))
        assert r.status_code == 200
        assert len(r.json()) == 0

    def test_female_1990_cung_can_match_tay_truc(
        self, client: TestClient, db: Session,
    ) -> None:
        """1990 nữ → Cấn (Tây tứ mệnh), Tây Nam là Sinh Khí."""
        token, tenant_id = _register(client, email="female@e2e.example.com")
        _grant_credit(db, tenant_id, 5)

        cust = client.post(
            "/v1/customers",
            headers=_auth_header(token),
            json={
                "full_name": "Bà Khách Nữ",
                "birth_date": "1990-08-15",
                "gender": "nu",
                "consent_given": True,
            },
        ).json()
        lt = client.post(
            "/v1/ocr/sodo",
            headers=_auth_header(token),
            files={"file": ("x.pdf", b"%PDF", "application/pdf")},
        ).json()
        client.patch(
            f"/v1/ocr/sodo/{lt['land_title_id']}/direction",
            headers=_auth_header(token),
            json={"house_direction": "Tây Nam"},
        )
        r = client.post(
            "/v1/reports",
            headers=_auth_header(token),
            json={
                "customer_id": cust["id"],
                "land_title_id": lt["land_title_id"],
                "purposes": ["nhap_trach"],
                "good_day_window_start": "2026-07-01",
                "good_day_window_end": "2026-07-31",
            },
        )
        assert r.status_code == 201, r.text
        data = r.json()["result_data"]
        assert data["cung_menh"]["cung"] == "Cấn"
        assert data["cung_menh"]["nhom"] == "Tây tứ mệnh"
        assert data["house_match"]["matched_quality"] == "Sinh Khí"
