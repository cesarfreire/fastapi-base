from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class GroupBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None


class GroupCreateSchema(GroupBaseSchema):
    pass


class GroupResponseSchema(GroupBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class GroupDetailsSchema(GroupResponseSchema):
    users: List['UserResponseSchema']  # noqa: F821
    roles: List['RoleResponseSchema']  # noqa: F821

    model_config = ConfigDict(from_attributes=True)


class GroupListResponseSchema(BaseModel):
    groups: List[GroupResponseSchema]
