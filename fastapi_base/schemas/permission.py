from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from fastapi_base.schemas.role import RoleDetailsSchema


class PermissionBaseSchema(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


class PermissionCreateSchema(PermissionBaseSchema):
    pass


class PermissionResponseSchema(PermissionBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PermissionListResponseSchema(BaseModel):
    permissions: list[PermissionResponseSchema]


RoleDetailsSchema.model_rebuild()
