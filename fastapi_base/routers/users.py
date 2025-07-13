from http import HTTPStatus
from logging import getLogger
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.database import get_session
from fastapi_base.models import User
from fastapi_base.schemas.filters import FilterParams
from fastapi_base.schemas.response import Response
from fastapi_base.schemas.user import (
    UserCreateSchema,
    UserDetailsSchema,
    UserListResponseSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from fastapi_base.security import (
    create_audit_log,
    get_password_hash,
    require_permission,
)

users_router = APIRouter(prefix='/users', tags=['users'])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(require_permission('users', 'create'))]

logger = getLogger('uvicorn.error')


@users_router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=UserResponseSchema
)
async def create_user(
    user: UserCreateSchema,
    background_tasks: BackgroundTasks,
    session: Session,
    # current_user: User = Depends(require_permission("users", "create")),
    request: Request = None,
):
    try:
        db_user = User(
            username=user.username,
            password=get_password_hash(user.password),
            email=user.email,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=db_user.id,
            action='create',
            resource_type='users',
            resource_id=db_user.id,
            details={'username': user.username, 'email': user.email},
            ip_address=request.client.host if request else None,
        )

        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Username or email already exists',
        )


@users_router.get(
    '/', status_code=HTTPStatus.OK, response_model=UserListResponseSchema
)
async def list_users(
    session: Session,
    filter_users: Annotated[FilterParams, Query()],
    current_user: Annotated[
        User, Depends(require_permission('users', 'list'))
    ],
):
    users = await session.scalars(
        select(User).offset(filter_users.offset).limit(filter_users.limit)
    )
    return {'users': users.all()}


@users_router.get(
    '/{user_id}',
    status_code=HTTPStatus.OK,
    response_model=UserDetailsSchema,
)
async def read_user(
    user_id: int,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('users', 'read'))
    ],
):
    db_user = await session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        logger.warning(f'User with id {user_id} not found.')
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    return db_user


@users_router.put(
    '/{user_id}',
    status_code=HTTPStatus.OK,
    response_model=UserResponseSchema,
)
async def update_user(
    user_id: int,
    user_update: UserUpdateSchema,
    session: Session,
    background_tasks: BackgroundTasks,
    current_user: Annotated[
        User, Depends(require_permission('users', 'update'))
    ],
    request: Request = None,
):
    db_user = await session.scalar(select(User).where(User.id == user_id))
    if not db_user:
        logger.warning(f'User with id {user_id} not found.')
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    update_data = user_update.model_dump(exclude_unset=True)

    try:
        if update_data:
            stmt = update(User).where(User.id == user_id).values(**update_data)
            await session.execute(stmt)
            await session.commit()

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        db_user = result.scalars().first()

        background_tasks.add_task(
            create_audit_log,
            db=session,
            user_id=current_user.id,
            action='update',
            resource_type='users',
            resource_id=user_id,
            details=update_data,
            ip_address=request.client.host if request else None,
        )
        return db_user
    except IntegrityError:
        logger.warning(
            f'Update failed for user {user_id} '
            f'due to duplicate username or email.'
        )
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Username or email already exists',
        )


@users_router.delete(
    '/{user_id}',
    status_code=HTTPStatus.OK,
    response_model=Response,
)
async def delete_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    session: Session,
    current_user: Annotated[
        User, Depends(require_permission('users', 'delete'))
    ],
    request: Request = None,
):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    db_user = result.scalars().first()

    if db_user is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    # Store username for audit log
    username = db_user.username

    stmt = delete(User).where(User.id == user_id)
    await session.execute(stmt)
    await session.commit()

    background_tasks.add_task(
        create_audit_log,
        db=session,
        user_id=None,
        action='delete',
        resource_type='users',
        resource_id=user_id,
        details={'username': username},
        ip_address=request.client.host if request else None,
    )

    return Response(message='User deleted successfully')
