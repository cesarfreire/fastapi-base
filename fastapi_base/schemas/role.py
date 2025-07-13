from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RoleBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreateSchema(RoleBaseSchema):
    pass


class RoleUpdateSchema(RoleBaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None


class RoleResponseSchema(RoleBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RoleDetailsSchema(RoleResponseSchema):
    permissions: List['PermissionResponseSchema']  # noqa: F821

    model_config = ConfigDict(from_attributes=True)


class RoleListResponseSchema(BaseModel):
    roles: List[RoleResponseSchema]
