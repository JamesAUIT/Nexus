"""Add drift_type, extend useful_links and runbooks, add reports and health checks

Revision ID: 003
Revises: 002
Create Date: 2025-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drift_findings", sa.Column("drift_type", sa.String(64), nullable=True))
    op.create_index("ix_drift_findings_drift_type", "drift_findings", ["drift_type"], unique=False)

    op.add_column("virtual_machines", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("virtual_machines", sa.Column("owner", sa.String(255), nullable=True))
    op.add_column("virtual_machines", sa.Column("tags", sa.String(512), nullable=True))
    op.add_column("hosts", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("hosts", sa.Column("owner", sa.String(255), nullable=True))
    op.add_column("hosts", sa.Column("tags", sa.String(512), nullable=True))

    op.add_column("useful_links", sa.Column("site_id", sa.Integer(), nullable=True))
    op.add_column("useful_links", sa.Column("required_permission", sa.String(64), nullable=True))
    op.add_column("useful_links", sa.Column("related_entity_type", sa.String(64), nullable=True))
    op.add_column("useful_links", sa.Column("related_entity_id", sa.String(255), nullable=True))
    op.create_foreign_key("fk_useful_links_site", "useful_links", "sites", ["site_id"], ["id"])
    op.create_index("ix_useful_links_site_id", "useful_links", ["site_id"], unique=False)

    op.add_column("runbooks", sa.Column("tags", sa.String(512), nullable=True))
    op.add_column("runbooks", sa.Column("related_systems", sa.Text(), nullable=True))
    op.add_column("runbooks", sa.Column("related_links", sa.Text(), nullable=True))

    op.create_table(
        "report_definitions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("query_params_schema", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_definitions_slug", "report_definitions", ["slug"], unique=True)

    op.create_table(
        "report_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_definition_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("params_json", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("result_path", sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(["report_definition_id"], ["report_definitions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_runs_report_definition_id", "report_runs", ["report_definition_id"], unique=False)

    op.create_table(
        "health_check_definitions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("check_type", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_check_definitions_slug", "health_check_definitions", ["slug"], unique=True)

    op.create_table(
        "health_check_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "health_check_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("health_check_run_id", sa.Integer(), nullable=False),
        sa.Column("definition_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("message", sa.String(1024), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["health_check_run_id"], ["health_check_runs.id"]),
        sa.ForeignKeyConstraint(["definition_id"], ["health_check_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_check_results_run_id", "health_check_results", ["health_check_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_health_check_results_run_id", "health_check_results")
    op.drop_table("health_check_results")
    op.drop_table("health_check_runs")
    op.drop_index("ix_health_check_definitions_slug", "health_check_definitions")
    op.drop_table("health_check_definitions")
    op.drop_index("ix_report_runs_report_definition_id", "report_runs")
    op.drop_table("report_runs")
    op.drop_index("ix_report_definitions_slug", "report_definitions")
    op.drop_table("report_definitions")
    op.drop_column("runbooks", "related_links")
    op.drop_column("runbooks", "related_systems")
    op.drop_column("runbooks", "tags")
    op.drop_index("ix_useful_links_site_id", "useful_links")
    op.drop_constraint("fk_useful_links_site", "useful_links", type_="foreignkey")
    op.drop_column("useful_links", "related_entity_id")
    op.drop_column("useful_links", "related_entity_type")
    op.drop_column("useful_links", "required_permission")
    op.drop_column("useful_links", "site_id")
    op.drop_column("hosts", "tags")
    op.drop_column("hosts", "owner")
    op.drop_column("hosts", "ip_address")
    op.drop_column("virtual_machines", "tags")
    op.drop_column("virtual_machines", "owner")
    op.drop_column("virtual_machines", "ip_address")
    op.drop_index("ix_drift_findings_drift_type", "drift_findings")
    op.drop_column("drift_findings", "drift_type")
