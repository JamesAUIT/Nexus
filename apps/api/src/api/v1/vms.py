from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import VirtualMachine
from src.schemas.virtual_machine import VirtualMachineResponse

router = APIRouter(prefix="/vms", tags=["vms"])


@router.get("", response_model=list[VirtualMachineResponse])
def list_vms(db: Session = Depends(get_db_session), current_user: User = Depends(require_permission("vms:read"))):
    return db.query(VirtualMachine).order_by(VirtualMachine.name).all()
