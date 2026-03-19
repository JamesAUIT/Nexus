"""Certificates, iDRAC/Redfish, change events, connectivity cache, scripts, link templates, favourites, recent

Revision ID: 005
Revises: 004
Create Date: 2025-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tls_certificates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("issuer", sa.String(512), nullable=True),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("not_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("days_until_expiry", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scan_error", sa.String(512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tls_certificates_hostname", "tls_certificates", ["hostname"], unique=False)
    op.create_index("ix_tls_certificates_severity", "tls_certificates", ["severity"], unique=False)
    op.create_index("ix_tls_certificates_not_after", "tls_certificates", ["not_after"], unique=False)

    op.create_table(
        "idrac_inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=True),
        sa.Column("connector_id", sa.Integer(), nullable=True),
        sa.Column("target_url", sa.String(512), nullable=True),
        sa.Column("bios_version", sa.String(128), nullable=True),
        sa.Column("idrac_version", sa.String(128), nullable=True),
        sa.Column("firmware_inventory", sa.Text(), nullable=True),
        sa.Column("compliance_status", sa.String(64), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scan_error", sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["connector_id"], ["connectors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_idrac_inventory_host_id", "idrac_inventory", ["host_id"], unique=False)

    op.create_table(
        "change_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("change_type", sa.String(64), nullable=False),
        sa.Column("field_name", sa.String(128), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_change_events_entity", "change_events", ["entity_type", "entity_id"], unique=False)
    op.create_index("ix_change_events_changed_at", "change_events", ["changed_at"], unique=False)

    op.create_table(
        "connectivity_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("target", sa.String(512), nullable=False),
        sa.Column("check_type", sa.String(32), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_connectivity_results_target_type", "connectivity_results", ["target", "check_type"], unique=False)

    op.create_table(
        "script_definitions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("script_type", sa.String(32), nullable=False),
        sa.Column("approved_only", sa.Boolean(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_script_definitions_slug", "script_definitions", ["slug"], unique=True)

    op.create_table(
        "script_executions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("script_definition_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["script_definition_id"], ["script_definitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_script_executions_script_id", "script_executions", ["script_definition_id"], unique=False)

    op.create_table(
        "link_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url_template", sa.String(2048), nullable=False),
        sa.Column("entity_types", sa.String(255), nullable=True),
        sa.Column("icon", sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_favourites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_favourites_user_entity", "user_favourites", ["user_id", "entity_type", "entity_id"], unique=True)

    op.create_table(
        "recent_objects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recent_objects_user", "recent_objects", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_recent_objects_user", "recent_objects")
    op.drop_table("recent_objects")
    op.drop_index("ix_user_favourites_user_entity", "user_favourites")
    op.drop_table("user_favourites")
    op.drop_table("link_templates")
    op.drop_index("ix_script_executions_script_id", "script_executions")
    op.drop_table("script_executions")
    op.drop_index("ix_script_definitions_slug", "script_definitions")
    op.drop_table("script_definitions")
    op.drop_index("ix_connectivity_results_target_type", "connectivity_results")
    op.drop_table("connectivity_results")
    op.drop_index("ix_change_events_changed_at", "change_events")
    op.drop_index("ix_change_events_entity", "change_events")
    op.drop_table("change_events")
    op.drop_index("ix_idrac_inventory_host_id", "idrac_inventory")
    op.drop_table("idrac_inventory")
    op.drop_index("ix_tls_certificates_not_after", "tls_certificates")
    op.drop_index("ix_tls_certificates_severity", "tls_certificates")
    op.drop_index("ix_tls_certificates_hostname", "tls_certificates")
    op.drop_table("tls_certificates")
