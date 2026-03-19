from pydantic import BaseModel


class SiteBase(BaseModel):
    name: str
    slug: str
    netbox_site_id: int | None = None


class SiteCreate(SiteBase):
    pass


class SiteResponse(SiteBase):
    id: int

    class Config:
        from_attributes = True
