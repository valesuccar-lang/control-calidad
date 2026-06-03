"""initial schema - 8 tables

Revision ID: 0001
Revises:
Create Date: 2026-06-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TABLE 1: users
    op.create_table(
        "users",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("email", sa.String(100), unique=True, nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # TABLE 2: fabrics
    op.create_table(
        "fabrics",
        sa.Column("fabric_id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fabrics_status", "fabrics", ["status"])

    # TABLE 3: lotes
    op.create_table(
        "lotes",
        sa.Column("lote_id", sa.String(50), primary_key=True),
        sa.Column("fabric_id", sa.String(50), sa.ForeignKey("fabrics.fabric_id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="positive_quantity"),
    )
    op.create_index("ix_lotes_status", "lotes", ["status"])
    op.create_index("ix_lotes_fabric_id", "lotes", ["fabric_id"])

    # TABLE 4: machines
    op.create_table(
        "machines",
        sa.Column("machine_id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_machines_status", "machines", ["status"])

    # TABLE 5: defects
    op.create_table(
        "defects",
        sa.Column("defect_id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), server_default="MEDIUM"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_defects_status", "defects", ["status"])
    op.create_index("ix_defects_category", "defects", ["category"])

    # TABLE 6: inspections
    op.create_table(
        "inspections",
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lote_id", sa.String(50), sa.ForeignKey("lotes.lote_id"), nullable=False),
        sa.Column("analista_id", sa.String(50), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("defect_id", sa.String(50), sa.ForeignKey("defects.defect_id"), nullable=False),
        sa.Column("comment_text", sa.String(500), nullable=False),
        sa.Column("photo_path", sa.String(500), nullable=False),
        sa.Column("photo_checksum", sa.String(64), nullable=False),
        sa.Column("machine_id", sa.String(50), sa.ForeignKey("machines.machine_id"), nullable=False),
        sa.Column("check_in", sa.TIMESTAMP, nullable=False),
        sa.Column("check_out", sa.TIMESTAMP),
        sa.Column("elapsed_seconds", sa.Integer),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("sync_attempts", sa.Integer, server_default="0"),
        sa.Column("last_sync_error", sa.String(500)),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("char_length(comment_text) >= 10", name="min_comment_length"),
    )
    op.create_index("ix_inspections_lote_id", "inspections", ["lote_id"])
    op.create_index("ix_inspections_analista_id", "inspections", ["analista_id"])
    op.create_index("ix_inspections_sync_status", "inspections", ["sync_status"])

    # TABLE 7: approvals
    op.create_table(
        "approvals",
        sa.Column("approval_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inspections.inspection_id"), nullable=False, unique=True),
        sa.Column("jefe_qa_id", sa.String(50), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("rejection_reason", sa.String(500)),
        sa.Column("notes", sa.Text),
        sa.Column("approved_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(decision = 'REJECTED' AND rejection_reason IS NOT NULL) OR decision = 'APPROVED'",
            name="rejection_reason_required"
        ),
    )
    op.create_index("ix_approvals_inspection_id", "approvals", ["inspection_id"])
    op.create_index("ix_approvals_jefe_qa_id", "approvals", ["jefe_qa_id"])

    # TABLE 8: audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("details", sa.Text),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False, server_default="SUCCESS"),
        sa.Column("error_message", sa.String(500)),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_user_action", "audit_logs", ["user_id", "action"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("approvals")
    op.drop_table("inspections")
    op.drop_table("defects")
    op.drop_table("machines")
    op.drop_table("lotes")
    op.drop_table("fabrics")
    op.drop_table("users")
