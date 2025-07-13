from http import HTTPStatus
from logging import getLogger
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_base.database import get_session
from fastapi_base.models import Group, Role, User
from fastapi_base.schemas.group import (
    GroupCreateSchema,
    GroupDetailsSchema,
    GroupListResponseSchema,
    GroupResponseSchema,
)
from fastapi_base.schemas.response import Response
from fastapi_base.security import (
    require_permission,
)

groups_router = APIRouter(prefix='/groups', tags=['groups'])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(require_permission('groups', 'create'))]

logger = getLogger('uvicorn.error')


@groups_router.post(
    '/', response_model=GroupResponseSchema, status_code=HTTPStatus.CREATED
)
async def create_group(
    group: GroupCreateSchema,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'create'))
    ],
):
    try:
        db_group = Group(**group.model_dump())
        session.add(db_group)
        await session.commit()
        await session.refresh(db_group)
        return db_group
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Group name already exists',
        )


@groups_router.get('/', response_model=GroupListResponseSchema)
async def get_groups(
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'list'))
    ],
    skip: int = 0,
    limit: int = 100,
):
    stmt = select(Group).offset(skip).limit(limit)
    result = await session.execute(stmt)
    groups = result.scalars().all()
    return {'groups': groups}


@groups_router.get('/{group_id}', response_model=GroupDetailsSchema)
async def get_group(
    group_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'read'))
    ],
):
    stmt = (
        select(Group)
        .options(selectinload(Group.users), selectinload(Group.roles))
        .where(Group.id == group_id)
    )
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    return group


@groups_router.delete('/{group_id}', response_model=GroupResponseSchema)
async def delete_group(
    group_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'delete'))
    ],
):
    stmt = select(Group).where(Group.id == group_id)
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    await session.delete(group)
    await session.commit()
    return group


@groups_router.put('/{group_id}', response_model=GroupResponseSchema)
async def update_group(
    group_id: int,
    group_update: GroupCreateSchema,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'update'))
    ],
):
    stmt = select(Group).where(Group.id == group_id)
    result = await session.execute(stmt)
    db_group = result.scalar_one_or_none()

    if not db_group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    update_data = group_update.model_dump(exclude_unset=True)

    if 'name' in update_data:
        existing_group = await session.scalar(
            select(Group).where(Group.name == update_data['name'])
        )
        if existing_group and existing_group.id != group_id:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Group name already exists',
            )

    for key, value in update_data.items():
        setattr(db_group, key, value)

    await session.commit()
    await session.refresh(db_group)
    return db_group


@groups_router.post(
    '/{group_id}/users/{user_id}',
    status_code=HTTPStatus.OK,
    response_model=Response,
)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'add_user'))
    ],
):
    stmt = (
        select(Group)
        .options(selectinload(Group.users))
        .where(Group.id == group_id)
    )
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    if any(user.id == user_id for user in group.users):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='User already in group'
        )

    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    group.users.append(user)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return {'message': 'User added to group successfully'}


@groups_router.delete(
    '/{group_id}/users/{user_id}',
    status_code=HTTPStatus.OK,
    response_model=Response,
)
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    session: Session,
):
    stmt = (
        select(Group)
        .options(selectinload(Group.users))
        .where(Group.id == group_id)
    )
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    user = next((u for u in group.users if u.id == user_id), None)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found in group'
        )

    group.users.remove(user)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return {'message': 'User removed from group successfully'}


@groups_router.post(
    '/{group_id}/roles/{role_id}',
    status_code=HTTPStatus.OK,
    response_model=Response,
)
async def assign_role_to_group(
    group_id: int,
    role_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'assign_role'))
    ],
):
    stmt = (
        select(Group)
        .options(selectinload(Group.roles))
        .where(Group.id == group_id)
    )
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    role = await session.get(Role, role_id)

    if not role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Role not found'
        )

    if role in group.roles:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Role already assigned to group',
        )

    group.roles.append(role)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return {'message': 'Role assigned to group successfully'}


@groups_router.delete(
    '/{group_id}/roles/{role_id}',
    status_code=HTTPStatus.OK,
    response_model=Response,
)
async def remove_role_from_group(
    group_id: int,
    role_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('groups', 'remove_role'))
    ],
):
    stmt = (
        select(Group)
        .options(selectinload(Group.roles))
        .where(Group.id == group_id)
    )
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Group not found'
        )

    role = next((r for r in group.roles if r.id == role_id), None)

    if not role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Role not found in group'
        )

    group.roles.remove(role)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return {'message': 'Role removed from group successfully'}
