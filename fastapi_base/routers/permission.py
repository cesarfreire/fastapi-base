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
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.database import get_session
from fastapi_base.models import Permission, Role, User
from fastapi_base.schemas.permission import (
    PermissionCreateSchema,
    PermissionListResponseSchema,
    PermissionResponseSchema,
)
from fastapi_base.schemas.response import Response
from fastapi_base.security import (
    create_audit_log,
    require_permission,
)

permissions_router = APIRouter(prefix='/permissions', tags=['permissions'])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[
    User, Depends(require_permission('permissions', 'create'))
]

logger = getLogger('uvicorn.error')


@permissions_router.post(
    '/',
    response_model=PermissionResponseSchema,
    status_code=HTTPStatus.CREATED,
)
async def create_permission(
    permission: PermissionCreateSchema,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('permissions', 'create'))
    ],
    request: Request = None,
):
    try:
        db_permission = Permission(**permission.model_dump())
        session.add(db_permission)
        await session.commit()
        await session.refresh(db_permission)

        # Log permission creation in background
        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=current_user.id,
            action='create',
            resource_type='permissions',
            resource_id=db_permission.id,
            details=permission.model_dump(),
            ip_address=request.client.host if request else None,
        )

        return db_permission
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Permission with this resource and action already exists',
        )


@permissions_router.get('/', response_model=PermissionListResponseSchema)
async def get_permissions(
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('permissions', 'list'))
    ],
    skip: int = 0,
    limit: int = 100,
):
    stmt = select(Permission).offset(skip).limit(limit)
    result = await session.execute(stmt)
    permissions = result.scalars().all()
    return {'permissions': permissions}


@permissions_router.get(
    '/{permission_id}', response_model=PermissionResponseSchema
)
async def get_permission(
    permission_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('permissions', 'read'))
    ],
):
    stmt = select(Permission).where(Permission.id == permission_id)
    result = await session.execute(stmt)
    db_permission = result.scalars().first()

    if db_permission is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Permission not found'
        )
    return db_permission


@permissions_router.put(
    '/{permission_id}', response_model=PermissionResponseSchema
)
async def update_permission(
    permission_id: int,
    permission_update: PermissionCreateSchema,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('permissions', 'update'))
    ],
    request: Request = None,
):
    stmt = select(Permission).where(Permission.id == permission_id)
    result = await session.execute(stmt)
    db_permission = result.scalars().first()

    if db_permission is None:
        raise HTTPException(status_code=404, detail='Permission not found')

    update_data = permission_update.model_dump()

    try:
        stmt = (
            update(Permission)
            .where(Permission.id == permission_id)
            .values(**update_data)
        )
        await session.execute(stmt)
        await session.commit()

        # Refresh permission data
        stmt = select(Permission).where(Permission.id == permission_id)
        result = await session.execute(stmt)
        db_permission = result.scalars().first()

        # Log permission update in background
        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=current_user.id,
            action='update',
            resource_type='permissions',
            resource_id=permission_id,
            details=update_data,
            ip_address=request.client.host if request else None,
        )

        return db_permission
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Permission with this resource and action already exists',
        )


@permissions_router.delete('/{permission_id}', status_code=HTTPStatus.OK)
async def delete_permission(
    permission_id: int,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('permissions', 'delete'))
    ],
    request: Request = None,
):
    stmt = select(Permission).where(Permission.id == permission_id)
    result = await session.execute(stmt)
    db_permission = result.scalars().first()

    if db_permission is None:
        raise HTTPException(status_code=404, detail='Permission not found')

    # Store permission details for audit log
    permission_details = {
        'name': db_permission.name,
        'resource': db_permission.resource,
        'action': db_permission.action,
    }

    stmt = delete(Permission).where(Permission.id == permission_id)
    await session.execute(stmt)
    await session.commit()

    # Log permission deletion in background
    background_tasks.add_task(
        create_audit_log,
        db=session,
        user_id=current_user.id,
        action='delete',
        resource_type='permissions',
        resource_id=permission_id,
        details=permission_details,
        ip_address=request.client.host if request else None,
    )

    return Response(
        message='Permission deleted successfully',
    )


@permissions_router.post(
    '/{permission_id}/assign-to-role/{role_id}', status_code=HTTPStatus.OK
)
async def assign_permission_to_role(
    permission_id: int,
    role_id: int,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('permissions', 'assign'))
    ],
    request: Request = None,
):
    # Check if permission exists
    permission_stmt = select(Permission).where(Permission.id == permission_id)
    permission_result = await session.execute(permission_stmt)
    permission = permission_result.scalars().first()

    if permission is None:
        raise HTTPException(status_code=404, detail='Permission not found')

    # Check if role exists
    role_stmt = select(Role).where(Role.id == role_id)
    role_result = await session.execute(role_stmt)
    role = role_result.scalars().first()

    if role is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Role not found'
        )

    # Add permission to role if not already assigned
    if permission not in role.permissions:
        role.permissions.append(permission)
        await session.commit()

        # Log assignment in background
        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=current_user.id,
            action='assign',
            resource_type='permissions',
            resource_id=permission_id,
            details={'role_id': role_id, 'permission_id': permission_id},
            ip_address=request.client.host if request else None,
        )

    return {
        'message': f"Permission '{permission.name}'"
        f" assigned to role '{role.name}'"
    }
