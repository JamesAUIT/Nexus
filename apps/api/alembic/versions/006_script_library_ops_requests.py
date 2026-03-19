"""Script Library (params, RBAC) and Operations Requests

Revision ID: 006
Revises: 005
Create Date: 2025-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("script_definitions", sa.Column("parameters_schema", sa.Text(), nullable=True))
    op.add_column("script_definitions", sa.Column("required_permission", sa.String(64), nullable=True))

    op.create_table(
        "ops_request_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("request_type", sa.String(64), nullable=False),
        sa.Column("subject_template", sa.String(512), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=True),
        sa.Column("form_schema", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ops_request_templates_slug", "ops_request_templates", ["slug"], unique=True)

    op.create_table(
        "ops_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("request_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("form_data", sa.Text(), nullable=True),
        sa.Column("recipient", sa.String(512), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["template_id"], ["ops_request_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ops_requests_status", "ops_requests", ["status"], unique=False)
    op.create_index("ix_ops_requests_created_at", "ops_requests", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ops_requests_created_at", "ops_requests")
    op.drop_index("ix_ops_requests_status", "ops_requests")
    op.drop_table("ops_requests")
    op.drop_index("ix_ops_request_templates_slug", "ops_request_templates")
    op.drop_table("ops_request_templates")
    op.drop_column("script_definitions", "required_permission")
    op.drop_column("script_definitions", "parameters_schema")
