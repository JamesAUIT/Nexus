"""Proxmox Explorer and Cloud Ops tables: snapshots, findings, tasks, entity cache; snapshot acks, HAProxy config

Revision ID: 004
Revises: 003
Create Date: 2025-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "proxmox_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("node_name", sa.String(128), nullable=False),
        sa.Column("vm_id", sa.Integer(), nullable=False),
        sa.Column("vm_name", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proxmox_snapshots_cluster_id", "proxmox_snapshots", ["cluster_id"], unique=False)
    op.create_index("ix_proxmox_snapshots_vm_id", "proxmox_snapshots", ["vm_id"], unique=False)
    op.create_index("ix_proxmox_snapshots_created_at", "proxmox_snapshots", ["created_at"], unique=False)

    op.create_table(
        "proxmox_findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("finding_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proxmox_findings_cluster_id", "proxmox_findings", ["cluster_id"], unique=False)
    op.create_index("ix_proxmox_findings_finding_type", "proxmox_findings", ["finding_type"], unique=False)

    op.create_table(
        "proxmox_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("node_name", sa.String(128), nullable=False),
        sa.Column("upid", sa.String(128), nullable=True),
        sa.Column("type", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user", sa.String(128), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proxmox_tasks_cluster_id", "proxmox_tasks", ["cluster_id"], unique=False)
    op.create_index("ix_proxmox_tasks_status", "proxmox_tasks", ["status"], unique=False)

    op.create_table(
        "proxmox_entities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("data", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proxmox_entities_cluster_kind", "proxmox_entities", ["cluster_id", "kind"], unique=False)

    op.create_table(
        "snapshot_acknowledgements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("vm_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_name", sa.String(255), nullable=True),
        sa.Column("ack_by", sa.String(255), nullable=False),
        sa.Column("ack_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshot_ack_cluster_vm", "snapshot_acknowledgements", ["cluster_id", "vm_id"], unique=False)

    op.create_table(
        "haproxy_config_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("config_content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_haproxy_config_cluster", "haproxy_config_versions", ["cluster_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_haproxy_config_cluster", "haproxy_config_versions")
    op.drop_table("haproxy_config_versions")
    op.drop_index("ix_snapshot_ack_cluster_vm", "snapshot_acknowledgements")
    op.drop_table("snapshot_acknowledgements")
    op.drop_index("ix_proxmox_entities_cluster_kind", "proxmox_entities")
    op.drop_table("proxmox_entities")
    op.drop_index("ix_proxmox_tasks_status", "proxmox_tasks")
    op.drop_index("ix_proxmox_tasks_cluster_id", "proxmox_tasks")
    op.drop_table("proxmox_tasks")
    op.drop_index("ix_proxmox_findings_finding_type", "proxmox_findings")
    op.drop_index("ix_proxmox_findings_cluster_id", "proxmox_findings")
    op.drop_table("proxmox_findings")
    op.drop_index("ix_proxmox_snapshots_created_at", "proxmox_snapshots")
    op.drop_index("ix_proxmox_snapshots_vm_id", "proxmox_snapshots")
    op.drop_index("ix_proxmox_snapshots_cluster_id", "proxmox_snapshots")
    op.drop_table("proxmox_snapshots")
