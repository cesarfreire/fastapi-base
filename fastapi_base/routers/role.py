from http import HTTPStatus
from logging import getLogger
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.database import get_session
from fastapi_base.models import Role, User
from fastapi_base.schemas.role import (
    RoleCreateSchema,
    RoleListResponseSchema,
    RoleResponseSchema,
    RoleUpdateSchema,
)
from fastapi_base.security import (
    create_audit_log,
    require_permission,
)

roles_router = APIRouter(prefix='/roles', tags=['roles'])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(require_permission('roles', 'create'))]

logger = getLogger('uvicorn.error')


@roles_router.post(
    '/', response_model=RoleResponseSchema, status_code=HTTPStatus.CREATED
)
async def create_role(
    role: RoleCreateSchema,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('roles', 'create'))
    ],
    request: Request = None,
):
    try:
        db_role = Role(**role.model_dump())
        session.add(db_role)
        await session.commit()
        await session.refresh(db_role)

        # Log role creation in background
        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=current_user.id,
            action='create',
            resource_type='roles',
            resource_id=db_role.id,
            details=role.model_dump(),
            ip_address=request.client.host if request else None,
        )

        return db_role
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Role name already exists'
        )


# get_roles
@roles_router.get(
    '/', status_code=HTTPStatus.OK, response_model=RoleListResponseSchema
)
async def get_roles(
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('roles', 'list'))
    ],
    skip: int = 0,
    limit: int = 100,
):
    stmt = select(Role).offset(skip).limit(limit)
    result = await session.execute(stmt)
    roles = result.scalars().all()
    return {'roles': roles}


@roles_router.get('/{role_id}', response_model=RoleResponseSchema)
async def get_role(
    role_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('roles', 'read'))
    ],
):
    stmt = select(Role).where(Role.id == role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Role not found'
        )

    return role


@roles_router.delete('/{role_id}', response_model=RoleResponseSchema)
async def delete_role(
    role_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('roles', 'delete'))
    ],
):
    stmt = select(Role).where(Role.id == role_id)
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Role not found'
        )

    await session.delete(role)
    await session.commit()

    return role


@roles_router.put('/{role_id}', response_model=RoleResponseSchema)
async def update_role(
    role_id: int,
    role_update: RoleUpdateSchema,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('roles', 'update'))
    ],
    request: Request = None,
):
    stmt = select(Role).where(Role.id == role_id)
    result = await session.execute(stmt)
    db_role = result.scalar_one_or_none()

    if not db_role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Role not found'
        )

    update_data = role_update.model_dump()

    for key, value in update_data.items():
        setattr(db_role, key, value)

    try:
        await session.commit()
        await session.refresh(db_role)

        # Log role update in background
        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=current_user.id,
            action='update',
            resource_type='roles',
            resource_id=db_role.id,
            details=update_data,
            ip_address=request.client.host if request else None,
        )

        return db_role
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Role name already exists'
        )
