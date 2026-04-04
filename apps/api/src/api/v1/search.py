# Global search: mixed result types (VMs, hosts, IPs, racks, datastores, NetBox-linked)
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Site, Rack, Host, VirtualMachine, Datastore

router = APIRouter(prefix="/search", tags=["search"])


class SearchResultItem(BaseModel):
    type: str
    id: int | str
    title: str
    subtitle: str | None
    link: str


@router.get("", response_model=list[SearchResultItem])
def global_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    q_lower = q.lower().strip()
    results: list[SearchResultItem] = []

    # Sites
    for row in db.query(Site).filter(Site.name.ilike(f"%{q_lower}%") | Site.slug.ilike(f"%{q_lower}%")).limit(5):
        results.append(SearchResultItem(type="site", id=row.id, title=row.name, subtitle=row.slug, link=f"/sites?highlight={row.id}"))

    # Racks
    for row in db.query(Rack).filter(Rack.name.ilike(f"%{q_lower}%")).limit(5):
        results.append(SearchResultItem(type="rack", id=row.id, title=row.name, subtitle=f"Site ID {row.site_id}", link=f"/racks?highlight={row.id}"))

    # Hosts
    for row in db.query(Host).filter(or_(Host.name.ilike(f"%{q_lower}%"), Host.ip_address.ilike(f"%{q_lower}%"))).limit(5):
        results.append(SearchResultItem(type="host", id=row.id, title=row.name, subtitle=row.ip_address or row.type, link=f"/hosts?highlight={row.id}"))

    # Virtual machines
    for row in db.query(VirtualMachine).filter(
        or_(VirtualMachine.name.ilike(f"%{q_lower}%"), VirtualMachine.ip_address.ilike(f"%{q_lower}%"))
    ).limit(5):
        results.append(SearchResultItem(type="virtual_machine", id=row.id, title=row.name, subtitle=row.power_state or row.ip_address, link=f"/vms?highlight={row.id}"))

    # Datastores
    for row in db.query(Datastore).filter(Datastore.name.ilike(f"%{q_lower}%")).limit(5):
        results.append(SearchResultItem(type="datastore", id=row.id, title=row.name, subtitle=row.type, link=f"/storage?highlight={row.id}"))

    return results
