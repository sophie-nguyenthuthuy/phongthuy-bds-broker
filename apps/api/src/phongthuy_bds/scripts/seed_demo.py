"""Seed demo data — tạo 1 sàn môi giới + 1 owner + 1 broker + sample customer."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from phongthuy_bds.core.security import encrypt_pii, hash_password
from phongthuy_bds.db.models import (
    Customer,
    LandTitle,
    Tenant,
    User,
    UserRole,
)
from phongthuy_bds.db.session import SessionLocal


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.execute(
            select(Tenant).where(Tenant.name == "Sàn BĐS Demo")
        ).scalar_one_or_none()
        if existing:
            print("Seed đã chạy trước đó — bỏ qua.")
            return

        tenant = Tenant(
            name="Sàn BĐS Demo",
            domain="demo.phongthuy-bds.vn",
            tax_code="0312345678",
            credit_balance=Decimal("100"),
        )
        db.add(tenant)
        db.flush()

        owner = User(
            tenant_id=tenant.id,
            email="owner@demo.local",
            full_name="Trần Chủ Sàn",
            phone="0901234567",
            hashed_password=hash_password("changeme123"),
            role=UserRole.OWNER,
        )
        broker = User(
            tenant_id=tenant.id,
            email="broker@demo.local",
            full_name="Lê Thị Môi Giới",
            phone="0907654321",
            hashed_password=hash_password("changeme123"),
            role=UserRole.BROKER,
        )
        db.add_all([owner, broker])
        db.flush()

        # Sample customer (đã có consent).
        customer = Customer(
            tenant_id=tenant.id,
            full_name_encrypted=encrypt_pii("Nguyễn Văn Khách"),
            phone_encrypted=encrypt_pii("0912345678"),
            birth_date_encrypted=encrypt_pii(date(1990, 8, 15).isoformat()),
            gender="nam",
            consent_given_at=datetime.now(UTC),
            delete_after=date.today() + timedelta(days=90),
        )
        db.add(customer)

        # Sample sổ đỏ.
        land = LandTitle(
            tenant_id=tenant.id,
            upload_storage_key="uploads/sodo/demo/sample.pdf",
            template_version="tt10_2024",
            so_seri="CT 123456",
            so_vao_so="CS-12345",
            extracted_data={
                "nguoi_su_dung": "Trần Chủ Nhà",
                "thua_dat_so": "123",
                "to_ban_do_so": "45",
                "dia_chi": "Số 10, đường Lê Lợi, P. Bến Nghé, Q.1, TP.HCM",
                "dien_tich_m2": "78.50",
                "muc_dich_su_dung": "ODT",
            },
            confidence=Decimal("0.92"),
            house_direction="Đông Nam",
            address="Số 10, đường Lê Lợi, P. Bến Nghé, Q.1, TP.HCM",
            area_m2=Decimal("78.50"),
        )
        db.add(land)

        db.commit()
        print("✓ Seed thành công:")
        print(f"  Tenant ID: {tenant.id}")
        print("  Owner    : owner@demo.local / changeme123")
        print("  Broker   : broker@demo.local / changeme123")
        print(f"  Credit   : {tenant.credit_balance}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
