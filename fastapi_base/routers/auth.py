from http import HTTPStatus
from logging import getLogger
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.database import get_session
from fastapi_base.models import User
from fastapi_base.schemas.jwt import JWTToken
from fastapi_base.security import (
    create_access_token,
    create_audit_log,
    get_current_active_user,
    verify_password,
)

auth_router = APIRouter(prefix='/auth', tags=['auth'])

Session = Annotated[AsyncSession, Depends(get_session)]
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
CurrentUser = Annotated[User, Depends(get_current_active_user)]

logger = getLogger('uvicorn.error')


@auth_router.post('/token', response_model=JWTToken, status_code=HTTPStatus.OK)
async def login_for_access_token(
    background_tasks: BackgroundTasks,
    session: Session,
    form_data: OAuth2Form,
    request: Request = None,
):
    user = await session.scalar(
        select(User).where(User.email == form_data.username)
    )

    if not user:
        logger.warning(f'User {form_data.username} not found.')
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password',
        )

    if not verify_password(form_data.password, user.password):
        logger.warning(f'Incorrect password for user {form_data.username}.')
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password',
        )

    access_token = create_access_token(data={'sub': user.email})

    background_tasks.add_task(
        create_audit_log,
        db=session,
        user_id=user.id,
        action='login',
        resource_type='auth',
        details={'success': True},
        ip_address=request.client.host if request else None,
    )

    return JWTToken(
        access_token=access_token,
        token_type='Bearer',
    )


@auth_router.post('/refresh_token', response_model=JWTToken)
async def refresh_access_token(user: CurrentUser):
    new_access_token = create_access_token(data={'sub': user.email})

    return {'access_token': new_access_token, 'token_type': 'Bearer'}


# @auth_router.get('/check-permission')
# async def check_user_permission(
#     resource: str,
#     action: str,
#     session: Session,
#     current_user: Annotated[User, Depends(get_current_active_user)],
#     resource_id: Optional[int] = None,
#     request: Request = None,
# ):
#     context = {
#         'current_time': datetime.now().time(),
#         'ip_address': request.client.host if request else None,
#     }
#
#     has_access = await has_permission(
#         user=current_user,
#         resource=resource,
#         action=action,
#         resource_id=resource_id,
#         context=context,
#     )
#
#     return {'has_permission': has_access}
