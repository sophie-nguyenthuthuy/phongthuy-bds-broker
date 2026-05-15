"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-15
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ─── tenants ─────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("tax_code", sa.String(20), nullable=True),
        sa.Column("credit_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("domain"),
    )

    # ─── users ───────────────────────────────────────────────────
    user_role = sa.Enum("owner", "admin", "broker", "viewer", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="broker"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # ─── customers ───────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("full_name_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("phone_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("birth_date_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("gender", sa.String(8), nullable=False),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_doc_url", sa.String(512), nullable=True),
        sa.Column("delete_after", sa.Date, nullable=False),
    )
    op.create_index("ix_customers_delete_after", "customers", ["delete_after"])

    # ─── land_titles ─────────────────────────────────────────────
    op.create_table(
        "land_titles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("upload_storage_key", sa.String(512), nullable=False),
        sa.Column("template_version", sa.String(32), nullable=False),
        sa.Column("so_seri", sa.String(64), nullable=True),
        sa.Column("so_vao_so", sa.String(64), nullable=True),
        sa.Column("extracted_data", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("house_direction", sa.String(16), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("area_m2", sa.Numeric(10, 2), nullable=True),
    )

    # ─── reports ─────────────────────────────────────────────────
    report_status = sa.Enum(
        "pending", "ocr_running", "ocr_done", "computing", "ready", "failed",
        name="report_status",
    )
    report_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("land_title_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("land_titles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("status", report_status, nullable=False, server_default="pending"),
        sa.Column("purposes", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("result_data", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("pdf_storage_key", sa.String(512), nullable=True),
        sa.Column("credit_cost", sa.Numeric(8, 2), nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    # ─── credit_transactions ─────────────────────────────────────
    op.create_table(
        "credit_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(12, 2), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("payment_provider", sa.String(32), nullable=True),
        sa.Column("payment_data", postgresql.JSON, nullable=False, server_default="{}"),
    )
    op.create_index(
        "uq_credit_tx_reference",
        "credit_transactions",
        ["reference"],
        unique=True,
        postgresql_where=sa.text("reference IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_credit_tx_reference", table_name="credit_transactions")
    op.drop_table("credit_transactions")
    op.drop_table("reports")
    sa.Enum(name="report_status").drop(op.get_bind(), checkfirst=True)
    op.drop_table("land_titles")
    op.drop_index("ix_customers_delete_after", table_name="customers")
    op.drop_table("customers")
    op.drop_table("users")
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
    op.drop_table("tenants")
