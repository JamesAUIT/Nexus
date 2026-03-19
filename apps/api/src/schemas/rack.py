from pydantic import BaseModel


class RackBase(BaseModel):
    site_id: int
    name: str
    netbox_rack_id: int | None = None


class RackCreate(RackBase):
    pass


class RackResponse(RackBase):
    id: int

    class Config:
        from_attributes = True
