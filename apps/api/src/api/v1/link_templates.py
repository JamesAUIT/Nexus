# Link templates for Grafana / Log Insight deep links (configurable URL templates)
from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
from urllib.parse import quote

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import LinkTemplate, VirtualMachine, Host, Datastore

router = APIRouter(prefix="/link-templates", tags=["link-templates"])


@router.get("")
def list_templates(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    rows = db.query(LinkTemplate).order_by(LinkTemplate.name).all()
    return {"data": [{"id": t.id, "name": t.name, "url_template": t.url_template, "entity_types": t.entity_types, "icon": t.icon} for t in rows]}


@router.get("/resolve")
def resolve_url(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    template_id: int = Query(...),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    template = db.query(LinkTemplate).filter(LinkTemplate.id == template_id).first()
    if not template:
        return {"url": None, "error": "Template not found"}
    params = {}
    if entity_type == "vm":
        try:
            eid = int(entity_id)
        except ValueError:
            return {"url": None, "error": "Invalid entity_id"}
        vm = db.query(VirtualMachine).filter(VirtualMachine.id == eid).first()
        if vm:
            params = {"name": vm.name, "id": str(vm.id), "host": ""}
            if vm.host_id:
                h = db.query(Host).filter(Host.id == vm.host_id).first()
                if h:
                    params["host"] = h.name
    elif entity_type == "host":
        h = db.query(Host).filter(Host.id == int(entity_id)).first()
        if h:
            params = {"name": h.name, "id": str(h.id)}
    elif entity_type == "datastore":
        d = db.query(Datastore).filter(Datastore.id == int(entity_id)).first()
        if d:
            params = {"name": d.name, "id": str(d.id)}
    url = template.url_template
    for k, v in params.items():
        url = url.replace("{{" + k + "}}", quote(str(v)))
    return {"url": url}
