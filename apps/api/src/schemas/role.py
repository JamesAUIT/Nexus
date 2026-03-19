import json
from pydantic import BaseModel, field_validator


class RoleBase(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str] = []


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    permissions: list[str] = []

    class Config:
        from_attributes = True

    @field_validator("permissions", mode="before")
    @classmethod
    def parse_permissions(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return []
