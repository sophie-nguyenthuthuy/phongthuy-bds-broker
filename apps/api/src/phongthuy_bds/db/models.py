"""ORM models — multi-tenant, encrypted PII fields."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    LargeBinary,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from phongthuy_bds.db.base import Base, TimestampMixin, UUIDPKMixin


class UserRole(StrEnum):
    OWNER = "owner"            # Chủ sàn môi giới
    ADMIN = "admin"            # Quản trị
    BROKER = "broker"          # Môi giới
    VIEWER = "viewer"          # Xem báo cáo (read-only)


class ReportStatus(StrEnum):
    PENDING = "pending"
    OCR_RUNNING = "ocr_running"
    OCR_DONE = "ocr_done"
    COMPUTING = "computing"
    READY = "ready"
    FAILED = "failed"


class Purpose(StrEnum):
    DONG_THO = "dong_tho"
    NHAP_TRACH = "nhap_trach"
    KHAI_TRUONG = "khai_truong"
    DAT_MONG = "dat_mong"


# ─── Tenant (mỗi sàn môi giới = 1 tenant) ─────────────────────────
class Tenant(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    tax_code: Mapped[str | None] = mapped_column(String(20))         # MST
    credit_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


# ─── User (môi giới) ──────────────────────────────────────────────
class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.BROKER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    __table_args__ = ({"sqlite_autoincrement": True},)  # placeholder for unique constraint


# ─── Customer (DLCN — encrypted at rest) ──────────────────────────
class Customer(Base, UUIDPKMixin, TimestampMixin):
    """Khách hàng môi giới đang chào.

    Theo NĐ 13/2023/NĐ-CP: ngày sinh + CCCD là DLCN. Lưu mã hóa.
    Có endpoint xóa theo yêu cầu KH; retention mặc định 90 ngày.
    """
    __tablename__ = "customers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    full_name_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    phone_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    birth_date_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    gender: Mapped[str] = mapped_column(String(8), nullable=False)        # 'nam' | 'nu'
    consent_given_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    consent_doc_url: Mapped[str | None] = mapped_column(String(512))
    delete_after: Mapped[date] = mapped_column(
        Date, nullable=False,
        doc="Ngày bắt buộc xóa theo retention policy / DLCN",
    )


# ─── Sổ đỏ ───────────────────────────────────────────────────────
class LandTitle(Base, UUIDPKMixin, TimestampMixin):
    """Sổ đỏ đã OCR.

    Trường extracted_data theo schema TT 10/2024/TT-BTNMT (mẫu mới)
    hoặc TT 23/2014/TT-BTNMT (mẫu cũ).
    """
    __tablename__ = "land_titles"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    upload_storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    template_version: Mapped[str] = mapped_column(
        String(32), nullable=False, doc="tt23_2014 | tt10_2024",
    )
    so_seri: Mapped[str | None] = mapped_column(String(64))
    so_vao_so: Mapped[str | None] = mapped_column(String(64))
    extracted_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    house_direction: Mapped[str | None] = mapped_column(
        String(16), doc="Hướng nhà do môi giới xác nhận sau khi OCR",
    )
    address: Mapped[str | None] = mapped_column(Text)
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))


# ─── Report ──────────────────────────────────────────────────────
class Report(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    land_title_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("land_titles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"),
        nullable=False, default=ReportStatus.PENDING,
    )
    purposes: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list,
        doc="Danh sách Purpose: dong_tho | nhap_trach | …",
    )
    result_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    pdf_storage_key: Mapped[str | None] = mapped_column(String(512))
    credit_cost: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), nullable=False, default=Decimal("1"),
    )
    error_message: Mapped[str | None] = mapped_column(Text)


# ─── Credit / billing ────────────────────────────────────────────
class CreditTransaction(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "credit_transactions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False,
        doc="Dương = nạp, âm = trừ tín dụng khi tạo báo cáo",
    )
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(16), nullable=False,
        doc="topup | report | refund | adjustment",
    )
    reference: Mapped[str | None] = mapped_column(String(255))
    payment_provider: Mapped[str | None] = mapped_column(String(32))  # vnpay | momo | zalopay
    payment_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
