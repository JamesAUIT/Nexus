from pydantic import BaseModel


class HostBase(BaseModel):
    cluster_id: int | None = None
    site_id: int | None = None
    name: str
    type: str
    external_id: str | None = None


class HostCreate(HostBase):
    pass


class HostResponse(HostBase):
    id: int

    class Config:
        from_attributes = True
