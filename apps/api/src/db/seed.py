# Cloud Nexus - Seed data (run when DEMO_MODE or SEED_DB=1)
import json
import os
import sys

# Ensure we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from src.config import settings
from src.db.session import SessionLocal, init_db
from datetime import datetime, timezone, timedelta
from src.models import (
    Role, User, Site, Rack, Cluster, Host, VirtualMachine,
    Connector, SyncJob, UsefulLink, Runbook,
    ReportDefinition, HealthCheckDefinition,
    ProxmoxSnapshot, ProxmoxTask, BackupStatus, Datastore,
    LinkTemplate, ScriptDefinition, ChangeEvent,
    OpsRequestTemplate,
)
from src.core.security import hash_password
from src.core.encryption import encrypt_connector_config


def seed() -> None:
    if not (settings.demo_mode or getattr(settings, "seed_db", False)):
        try:
            seed_db = os.environ.get("SEED_DB", "0").strip().lower() in ("1", "true", "yes")
        except Exception:
            seed_db = False
        if not seed_db:
            print("Skipping seed: set DEMO_MODE=true or SEED_DB=1 to run.")
            return

    init_db()
    db: Session = SessionLocal()
    try:
        # Admin role with full permissions
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Full access",
                permissions=json.dumps(["admin:all"]),
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        # Break-glass local admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            pw = settings.admin_password
            if settings.demo_mode and pw == "changeme":
                pw = "admin"
            admin_user = User(
                username="admin",
                email="admin@localhost",
                hashed_password=hash_password(pw),
                role_id=admin_role.id,
                is_local=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("Created admin user (change password in production).")
        else:
            print("Admin user already exists.")

        # Sample site
        site = db.query(Site).filter(Site.slug == "dc1").first()
        if not site:
            site = Site(name="DC1", slug="dc1")
            db.add(site)
            db.commit()
            db.refresh(site)
            print("Created sample site DC1.")

        # Sample rack
        if db.query(Rack).filter(Rack.site_id == site.id, Rack.name == "R01").first() is None:
            db.add(Rack(site_id=site.id, name="R01"))
            db.commit()
            print("Created sample rack R01.")

        # Sample cluster
        cluster = db.query(Cluster).filter(Cluster.site_id == site.id, Cluster.name == "proxmox-cluster-1").first()
        if not cluster:
            cluster = Cluster(site_id=site.id, name="proxmox-cluster-1", type="proxmox")
            db.add(cluster)
            db.commit()
            db.refresh(cluster)
            print("Created sample cluster proxmox-cluster-1.")

        # Sample host
        if db.query(Host).filter(Host.cluster_id == cluster.id, Host.name == "pve1").first() is None:
            db.add(Host(cluster_id=cluster.id, site_id=site.id, name="pve1", type="hypervisor"))
            db.commit()
            print("Created sample host pve1.")

        # Sample VM
        host = db.query(Host).filter(Host.cluster_id == cluster.id).first()
        vm = None
        if host and db.query(VirtualMachine).filter(VirtualMachine.host_id == host.id, VirtualMachine.name == "demo-vm").first() is None:
            vm = VirtualMachine(host_id=host.id, cluster_id=cluster.id, name="demo-vm", power_state="running")
            db.add(vm)
            db.commit()
            db.refresh(vm)
            print("Created sample VM demo-vm.")
        else:
            vm = db.query(VirtualMachine).filter(VirtualMachine.cluster_id == cluster.id, VirtualMachine.name == "demo-vm").first()

        if cluster and vm and db.query(ProxmoxSnapshot).filter(ProxmoxSnapshot.cluster_id == cluster.id).first() is None:
            db.add(ProxmoxSnapshot(cluster_id=cluster.id, node_name=host.name if host else "pve1", vm_id=vm.id, vm_name=vm.name, name="pre-upgrade", created_at=datetime.now(timezone.utc) - timedelta(days=45), size_bytes=1024 * 1024 * 500))
            db.add(ProxmoxSnapshot(cluster_id=cluster.id, node_name=host.name if host else "pve1", vm_id=vm.id, vm_name=vm.name, name="daily", created_at=datetime.now(timezone.utc) - timedelta(days=1), size_bytes=1024 * 1024 * 200))
            db.commit()
            print("Created sample Proxmox snapshots.")
        if cluster and db.query(ProxmoxTask).filter(ProxmoxTask.cluster_id == cluster.id).first() is None:
            db.add(ProxmoxTask(cluster_id=cluster.id, node_name=host.name if host else "pve1", type="vzstart", status="stopped", start_time=datetime.now(timezone.utc) - timedelta(hours=2), end_time=datetime.now(timezone.utc) - timedelta(hours=2) + timedelta(seconds=30), user="root@pam"))
            db.commit()
            print("Created sample Proxmox task.")
        if vm and db.query(BackupStatus).filter(BackupStatus.entity_type == "vm", BackupStatus.entity_id == str(vm.id)).first() is None:
            db.add(BackupStatus(entity_type="vm", entity_id=str(vm.id), status="ok", last_run_at=datetime.now(timezone.utc) - timedelta(days=2), details="last backup ok"))
            db.commit()
            print("Created sample backup status.")

        # Sample connectors and sync job
        conn = db.query(Connector).filter(Connector.name == "NetBox DC1").first()
        if not conn:
            config = encrypt_connector_config(json.dumps({"url": "https://netbox.example.com", "token": "stub"}))
            conn = Connector(
                type="netbox",
                name="NetBox DC1",
                base_url="https://netbox.example.com",
                encrypted_config=config,
            )
            db.add(conn)
            db.commit()
            db.refresh(conn)
            print("Created sample connector NetBox DC1.")
        if conn and db.query(SyncJob).filter(SyncJob.connector_id == conn.id).first() is None:
            db.add(SyncJob(connector_id=conn.id, schedule_cron="0 */6 * * *"))  # every 6h
            db.commit()
            print("Created sync job for NetBox DC1.")

        # Useful links (deep links to Grafana, Log Insight, etc.)
        for name, url, category in [
            ("Grafana", "https://grafana.example.com", "Monitoring"),
            ("Log Insight", "https://loginsight.example.com", "Logging"),
        ]:
            if db.query(UsefulLink).filter(UsefulLink.name == name).first() is None:
                db.add(UsefulLink(name=name, url=url, category=category))
        db.commit()
        print("Created useful links.")

        # Runbooks
        if db.query(Runbook).filter(Runbook.name == "VM Restart").first() is None:
            db.add(Runbook(name="VM Restart", content="1. Identify VM\n2. Graceful shutdown\n3. Start VM", category="Operations"))
            db.commit()
            print("Created sample runbook.")

        for slug, name, desc, check_type in [
            ("backup-coverage", "Backup coverage", "VMs without recent backup", "backup_coverage"),
            ("stale-snapshots", "Stale snapshots", "Snapshots older than threshold", "stale_snapshots"),
            ("missing-owners", "Missing owners", "VMs/hosts without owner", "missing_owners"),
            ("storage-threshold", "Storage threshold", "Datastores over capacity threshold", "storage_threshold"),
        ]:
            if db.query(HealthCheckDefinition).filter(HealthCheckDefinition.slug == slug).first() is None:
                db.add(HealthCheckDefinition(name=name, slug=slug, description=desc, check_type=check_type))
        db.commit()

        for slug, name, desc in [
            ("vm-inventory", "VM inventory", "All VMs with power state"),
            ("host-summary", "Host summary", "Hosts by cluster"),
        ]:
            if db.query(ReportDefinition).filter(ReportDefinition.slug == slug).first() is None:
                db.add(ReportDefinition(name=name, slug=slug, description=desc))
        db.commit()
        print("Created report and health check definitions.")

        for name, url_template, entity_types in [
            ("Grafana VM", "https://grafana.example.com/d/vm?var-vm={{name}}&var-host={{host}}", "vm"),
            ("Grafana Host", "https://grafana.example.com/d/host?var-host={{name}}", "host"),
            ("Log Insight VM", "https://loginsight.example.com/source?vm={{name}}", "vm"),
        ]:
            if db.query(LinkTemplate).filter(LinkTemplate.name == name).first() is None:
                db.add(LinkTemplate(name=name, url_template=url_template, entity_types=entity_types))
        db.commit()
        print("Created link templates.")

        for slug, name, script_type in [
            ("get-vm-info", "Get VM info (PowerShell)", "powershell"),
            ("host-health-check", "Host health check (PowerShell)", "powershell"),
        ]:
            if db.query(ScriptDefinition).filter(ScriptDefinition.slug == slug).first() is None:
                db.add(ScriptDefinition(name=name, slug=slug, description="Approved script only", script_type=script_type, approved_only=True, timeout_seconds=60, parameters_schema='[{"name":"target","type":"string","label":"Target"}]', required_permission="scripts:execute"))
        db.commit()
        print("Created script definitions.")

        for slug, name, req_type, subject, body in [
            ("datacenter-entry", "Datacenter entry request", "datacenter_entry", "Datacenter entry: {{reason}}", "<p>Request for datacenter entry.</p><p>Reason: {{reason}}</p><p>Date: {{date}}</p>"),
            ("asset-install", "Asset install", "asset_install", "Asset install: {{asset_type}}", "<p>Asset install request.</p><p>Type: {{asset_type}}</p><p>Location: {{location}}</p>"),
            ("asset-removal", "Asset removal", "asset_removal", "Asset removal: {{asset_id}}", "<p>Asset removal request.</p><p>Asset ID: {{asset_id}}</p>"),
        ]:
            if db.query(OpsRequestTemplate).filter(OpsRequestTemplate.slug == slug).first() is None:
                db.add(OpsRequestTemplate(name=name, slug=slug, request_type=req_type, subject_template=subject, body_template=body, form_schema='{"reason":"text","date":"date"}'))
        db.commit()
        print("Created ops request templates.")

        if vm and db.query(ChangeEvent).first() is None:
            db.add(ChangeEvent(entity_type="vm", entity_id=str(vm.id), change_type="created", changed_at=datetime.now(timezone.utc), changed_by="seed", source="seed"))
            db.commit()
            print("Created sample change event.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
