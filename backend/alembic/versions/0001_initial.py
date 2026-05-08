"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-08

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wa_session_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_wa_session_id", "sessions", ["wa_session_id"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wa_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("is_group", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("allowed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "wa_id", name="uq_user_wa"),
    )
    op.create_index("ix_contacts_user_id", "contacts", ["user_id"])
    op.create_index("ix_contacts_wa_id", "contacts", ["wa_id"])

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("suggest", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("auto_send", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("note", sa.String(500)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_permissions_user_id", "permissions", ["user_id"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("suggestion_id", sa.String(128), nullable=False),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id", ondelete="SET NULL")),
        sa.Column("incoming_message", sa.Text, nullable=False),
        sa.Column("original", sa.Text, nullable=False),
        sa.Column("edited", sa.Text, nullable=False),
        sa.Column("delta_json", sa.JSON),
        sa.Column("decision", sa.String(16), nullable=False, server_default="edit"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index("ix_feedback_suggestion_id", "feedback", ["suggestion_id"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("permissions")
    op.drop_table("contacts")
    op.drop_table("sessions")
    op.drop_table("users")
