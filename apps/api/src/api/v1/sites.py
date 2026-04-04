# Sites: list from DB (seed/demo or synced from NetBox)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models.site import Site
from src.schemas.site import SiteResponse

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteResponse])
def list_sites(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("sites:read")),
):
    sites = db.query(Site).order_by(Site.name).all()
    return sites
