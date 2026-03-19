from pydantic import BaseModel


class VirtualMachineBase(BaseModel):
    host_id: int | None = None
    cluster_id: int | None = None
    name: str
    external_id: str | None = None
    power_state: str | None = None


class VirtualMachineCreate(VirtualMachineBase):
    pass


class VirtualMachineResponse(VirtualMachineBase):
    id: int

    class Config:
        from_attributes = True
