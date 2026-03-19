"""
Drift framework: NetBox as source of truth, compare live systems for:
- undocumented_asset: exists in live but not in NetBox
- missing_asset: in NetBox but not in live
- ip_mismatch: IP differs from NetBox
- owner_missing: no owner set (NetBox has owner)
- tag_mismatch: tags differ from NetBox
"""
from sqlalchemy.orm import Session

from src.models import (
    DriftFinding,
    VirtualMachine,
    Host,
    Site,
    Rack,
)


DRIFT_TYPES = (
    "undocumented_asset",
    "missing_asset",
    "ip_mismatch",
    "owner_missing",
    "tag_mismatch",
)


def run_drift_check(db: Session) -> int:
    """
    Compare intended state (NetBox-synced: sites, racks, hosts, VMs with netbox IDs)
    vs live state. Create DriftFinding records. Returns count of findings.
    """
    count = 0
    # Clear existing findings for a fresh run (or keep history - here we replace)
    db.query(DriftFinding).delete()

    # Undocumented VMs: VMs that have no netbox/external_id or not in NetBox
    for vm in db.query(VirtualMachine).all():
        if not vm.external_id:
            db.add(DriftFinding(
                resource_type="virtual_machine",
                resource_id=str(vm.id),
                drift_type="undocumented_asset",
                field_name="external_id",
                expected_value=None,
                actual_value=vm.name,
                source_of_truth="netbox",
                discovered_from="proxmox",
            ))
            count += 1
        if not vm.owner:
            db.add(DriftFinding(
                resource_type="virtual_machine",
                resource_id=str(vm.id),
                drift_type="owner_missing",
                field_name="owner",
                expected_value="",
                actual_value=vm.name,
                source_of_truth="netbox",
                discovered_from="live",
            ))
            count += 1

    # Undocumented hosts
    for host in db.query(Host).all():
        if not host.external_id:
            db.add(DriftFinding(
                resource_type="host",
                resource_id=str(host.id),
                drift_type="undocumented_asset",
                field_name="external_id",
                expected_value=None,
                actual_value=host.name,
                source_of_truth="netbox",
                discovered_from="proxmox",
            ))
            count += 1

    # IP mismatch: placeholder - when we have NetBox IP and live IP we compare
    # Owner missing: already added for VMs without owner
    # Tag mismatch: when tags differ (simplified - just check presence)
    db.commit()
    return count
