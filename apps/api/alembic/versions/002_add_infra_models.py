"""Add racks, clusters, hosts, vms, datastores, storage_volumes, backup_statuses, drift_findings, useful_links, runbooks, saved_queries, sync_jobs, sync_job_runs

Revision ID: 002
Revises: 001
Create Date: 2025-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "racks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("netbox_rack_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_racks_site_id", "racks", ["site_id"], unique=False)
    op.create_index("ix_racks_name", "racks", ["name"], unique=False)

    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clusters_site_id", "clusters", ["site_id"], unique=False)
    op.create_index("ix_clusters_name", "clusters", ["name"], unique=False)
    op.create_index("ix_clusters_type", "clusters", ["type"], unique=False)

    op.create_table(
        "hosts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hosts_cluster_id", "hosts", ["cluster_id"], unique=False)
    op.create_index("ix_hosts_site_id", "hosts", ["site_id"], unique=False)
    op.create_index("ix_hosts_name", "hosts", ["name"], unique=False)
    op.create_index("ix_hosts_type", "hosts", ["type"], unique=False)

    op.create_table(
        "virtual_machines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("power_state", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"]),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_virtual_machines_host_id", "virtual_machines", ["host_id"], unique=False)
    op.create_index("ix_virtual_machines_cluster_id", "virtual_machines", ["cluster_id"], unique=False)
    op.create_index("ix_virtual_machines_name", "virtual_machines", ["name"], unique=False)

    op.create_table(
        "datastores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("host_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(64), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"]),
        sa.ForeignKeyConstraint(["host_id"], ["hosts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_datastores_cluster_id", "datastores", ["cluster_id"], unique=False)
    op.create_index("ix_datastores_host_id", "datastores", ["host_id"], unique=False)
    op.create_index("ix_datastores_name", "datastores", ["name"], unique=False)

    op.create_table(
        "storage_volumes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("datastore_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("capacity_bytes", sa.BigInteger(), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["datastore_id"], ["datastores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_storage_volumes_datastore_id", "storage_volumes", ["datastore_id"], unique=False)
    op.create_index("ix_storage_volumes_name", "storage_volumes", ["name"], unique=False)

    op.create_table(
        "backup_statuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("source_connector_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details", sa.String(1024), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_connector_id"], ["connectors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_backup_statuses_entity_type", "backup_statuses", ["entity_type"], unique=False)
    op.create_index("ix_backup_statuses_entity_id", "backup_statuses", ["entity_id"], unique=False)
    op.create_index("ix_backup_statuses_status", "backup_statuses", ["status"], unique=False)

    op.create_table(
        "drift_findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=False),
        sa.Column("field_name", sa.String(128), nullable=False),
        sa.Column("expected_value", sa.Text(), nullable=True),
        sa.Column("actual_value", sa.Text(), nullable=True),
        sa.Column("source_of_truth", sa.String(64), nullable=False),
        sa.Column("discovered_from", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drift_findings_resource_type", "drift_findings", ["resource_type"], unique=False)
    op.create_index("ix_drift_findings_resource_id", "drift_findings", ["resource_id"], unique=False)

    op.create_table(
        "useful_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_useful_links_name", "useful_links", ["name"], unique=False)
    op.create_index("ix_useful_links_category", "useful_links", ["category"], unique=False)

    op.create_table(
        "runbooks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_runbooks_name", "runbooks", ["name"], unique=False)
    op.create_index("ix_runbooks_category", "runbooks", ["category"], unique=False)

    op.create_table(
        "saved_queries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("query_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_queries_user_id", "saved_queries", ["user_id"], unique=False)
    op.create_index("ix_saved_queries_name", "saved_queries", ["name"], unique=False)

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("connector_id", sa.Integer(), nullable=False),
        sa.Column("schedule_cron", sa.String(64), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["connector_id"], ["connectors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_jobs_connector_id", "sync_jobs", ["connector_id"], unique=False)

    op.create_table(
        "sync_job_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sync_job_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.String(2048), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sync_job_id"], ["sync_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_job_runs_sync_job_id", "sync_job_runs", ["sync_job_id"], unique=False)
    op.create_index("ix_sync_job_runs_status", "sync_job_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sync_job_runs_status", "sync_job_runs")
    op.drop_index("ix_sync_job_runs_sync_job_id", "sync_job_runs")
    op.drop_table("sync_job_runs")
    op.drop_index("ix_sync_jobs_connector_id", "sync_jobs")
    op.drop_table("sync_jobs")
    op.drop_index("ix_saved_queries_name", "saved_queries")
    op.drop_index("ix_saved_queries_user_id", "saved_queries")
    op.drop_table("saved_queries")
    op.drop_index("ix_runbooks_category", "runbooks")
    op.drop_index("ix_runbooks_name", "runbooks")
    op.drop_table("runbooks")
    op.drop_index("ix_useful_links_category", "useful_links")
    op.drop_index("ix_useful_links_name", "useful_links")
    op.drop_table("useful_links")
    op.drop_index("ix_drift_findings_resource_id", "drift_findings")
    op.drop_index("ix_drift_findings_resource_type", "drift_findings")
    op.drop_table("drift_findings")
    op.drop_index("ix_backup_statuses_status", "backup_statuses")
    op.drop_index("ix_backup_statuses_entity_id", "backup_statuses")
    op.drop_index("ix_backup_statuses_entity_type", "backup_statuses")
    op.drop_table("backup_statuses")
    op.drop_index("ix_storage_volumes_name", "storage_volumes")
    op.drop_index("ix_storage_volumes_datastore_id", "storage_volumes")
    op.drop_table("storage_volumes")
    op.drop_index("ix_datastores_name", "datastores")
    op.drop_index("ix_datastores_host_id", "datastores")
    op.drop_index("ix_datastores_cluster_id", "datastores")
    op.drop_table("datastores")
    op.drop_index("ix_virtual_machines_name", "virtual_machines")
    op.drop_index("ix_virtual_machines_cluster_id", "virtual_machines")
    op.drop_index("ix_virtual_machines_host_id", "virtual_machines")
    op.drop_table("virtual_machines")
    op.drop_index("ix_hosts_type", "hosts")
    op.drop_index("ix_hosts_name", "hosts")
    op.drop_index("ix_hosts_site_id", "hosts")
    op.drop_index("ix_hosts_cluster_id", "hosts")
    op.drop_table("hosts")
    op.drop_index("ix_clusters_type", "clusters")
    op.drop_index("ix_clusters_name", "clusters")
    op.drop_index("ix_clusters_site_id", "clusters")
    op.drop_table("clusters")
    op.drop_index("ix_racks_name", "racks")
    op.drop_index("ix_racks_site_id", "racks")
    op.drop_table("racks")
