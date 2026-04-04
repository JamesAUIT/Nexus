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

    # IP mismatch: NetBox-synced host (nb-device-*) vs VM with same name
    for vm in db.query(VirtualMachine).filter(VirtualMachine.ip_address.isnot(None)).all():
        if not vm.name or not vm.ip_address:
            continue
        nbh = (
            db.query(Host)
            .filter(Host.name == vm.name, Host.external_id.isnot(None))
            .filter(Host.external_id.like("nb-device%"))
            .first()
        )
        if nbh and nbh.ip_address and nbh.ip_address.strip() != vm.ip_address.strip():
            db.add(
                DriftFinding(
                    resource_type="virtual_machine",
                    resource_id=str(vm.id),
                    drift_type="ip_mismatch",
                    field_name="ip_address",
                    expected_value=nbh.ip_address,
                    actual_value=vm.ip_address,
                    source_of_truth="netbox",
                    discovered_from="live",
                )
            )
            count += 1

    # Tag mismatch when both sides have tags
    for vm in db.query(VirtualMachine).filter(VirtualMachine.tags.isnot(None)).all():
        nbh = (
            db.query(Host)
            .filter(Host.name == vm.name, Host.external_id.like("nb-device%"))
            .first()
        )
        if nbh and nbh.tags and vm.tags and nbh.tags.strip() != vm.tags.strip():
            db.add(
                DriftFinding(
                    resource_type="virtual_machine",
                    resource_id=str(vm.id),
                    drift_type="tag_mismatch",
                    field_name="tags",
                    expected_value=nbh.tags[:512],
                    actual_value=vm.tags[:512],
                    source_of_truth="netbox",
                    discovered_from="live",
                )
            )
            count += 1

    db.commit()
    return count
