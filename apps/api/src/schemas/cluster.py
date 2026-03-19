from pydantic import BaseModel


class ClusterBase(BaseModel):
    site_id: int | None = None
    name: str
    type: str
    external_id: str | None = None


class ClusterCreate(ClusterBase):
    pass


class ClusterResponse(ClusterBase):
    id: int

    class Config:
        from_attributes = True
