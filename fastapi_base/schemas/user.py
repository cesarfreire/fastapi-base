from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from fastapi_base.schemas.group import GroupResponseSchema
from fastapi_base.schemas.role import RoleResponseSchema

MIN_PASSWORD_LENGTH = 8


class UserBaseSchema(BaseModel):
    username: str
    email: EmailStr


class UserCreateSchema(UserBaseSchema):
    password: str

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError(
                'Password must contain at least one uppercase letter'
            )
        if not any(char.islower() for char in v):
            raise ValueError(
                'Password must contain at least one lowercase letter'
            )
        if not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for char in v):
            raise ValueError(
                'Password must contain at least one special character'
            )
        return v


class UserResponseSchema(UserBaseSchema):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserListResponseSchema(BaseModel):
    users: List[UserResponseSchema]


class UserDetailsSchema(UserResponseSchema):
    roles: List['RoleResponseSchema']
    groups: List['GroupResponseSchema']

    model_config = ConfigDict(from_attributes=True)


class UserListSchema(BaseModel):
    users: list[UserResponseSchema]


# Update models
class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


# class PasswordChangeSchema(BaseModel):
#     current_password: str
#     new_password: str
#
#     @field_validator('new_password')
#     @classmethod
#     def password_strength(cls, v: str) -> str:
#         if len(v) < MIN_PASSWORD_LENGTH:
#             raise ValueError('Password must be at least 8 characters')
#         if not any(char.isdigit() for char in v):
#             raise ValueError('Password must contain at least one digit')
#         if not any(char.isupper() for char in v):
#             raise ValueError(
#                 'Password must contain at least one uppercase letter'
#             )
#         if not any(char.islower() for char in v):
#             raise ValueError(
#                 'Password must contain at least one lowercase letter'
#             )
#         if not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for char in v):
#             raise ValueError(
#                 'Password must contain at least one special character'
#             )
#         return v


UserDetailsSchema.model_rebuild()
