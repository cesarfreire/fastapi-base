from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.database import get_session
from fastapi_base.exceptions.auth import (
    CredentialsException,
    PermissionException,
    UserNotActiveException,
)
from fastapi_base.models import AuditLog, User
from fastapi_base.settings import Settings

pwd_context = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='/auth/token', refreshUrl='/auth/refresh'
)

settings = Settings()


def get_password_hash(password: str) -> str:
    """
    Hash a password using the recommended algorithm.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token with the given data.
    """
    to_encode = data.copy()

    expire = datetime.now(tz=ZoneInfo('America/Sao_Paulo')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({'exp': expire})
    encoded_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    """
    Decode the JWT token and return the user data.
    """
    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject_email = payload.get('sub')
        if not subject_email:
            raise CredentialsException
    except DecodeError:
        raise CredentialsException
    except ExpiredSignatureError:
        raise CredentialsException

    user = await session.scalar(
        select(User).where(User.email == subject_email)
    )

    if not user:
        raise CredentialsException

    return user


# Get current active user
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise UserNotActiveException
    return current_user


async def has_permission(
    user: User,
    resource: str,
    action: str,
    resource_id: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Check if user has permission to perform an action on a resource.
    Implements Attribute-Based Access Control (ABAC) by considering:
    - Direct user permissions
    - Role-based permissions
    - Group-based permissions
    - Contextual conditions
    """
    context = context or {}

    # Helper function to check conditions
    def evaluate_conditions(
        conditions: Optional[Dict[str, Any]], context: Dict[str, Any]
    ) -> bool:
        if not conditions:
            return True

        # Example condition: {"time_between": ["09:00", "17:00"]}
        for condition_key, condition_value in conditions.items():
            if condition_key == 'time_between':
                current_time = context.get(
                    'current_time', datetime.now().time()
                )
                start_time = datetime.strptime(
                    condition_value[0], '%H:%M'
                ).time()
                end_time = datetime.strptime(
                    condition_value[1], '%H:%M'
                ).time()
                if not (start_time <= current_time <= end_time):
                    return False
            elif condition_key == 'ip_range':
                ip = context.get('ip_address')
                if not ip or ip not in condition_value:
                    return False
            # Add more condition types as needed

        return True

    if user.is_superuser:
        # Superusers have all permissions
        return True

    # Check direct user permissions
    for permission in user.direct_permissions:
        if (
            permission.resource == resource
            and permission.action == action
            and evaluate_conditions(permission.conditions, context)
        ):
            return True

    # Check role-based permissions
    for role in user.roles:
        for permission in role.permissions:
            if (
                permission.resource == resource
                and permission.action == action
                and evaluate_conditions(permission.conditions, context)
            ):
                return True

    # Check group-based permissions (through roles)
    for group in user.groups:
        for role in group.roles:
            for permission in role.permissions:
                if (
                    permission.resource == resource
                    and permission.action == action
                    and evaluate_conditions(permission.conditions, context)
                ):
                    return True

    return False


def require_permission(resource: str, action: str):
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        request: Request = None,
    ):
        context = {
            'current_time': datetime.now().time(),
            'ip_address': request.client.host if request else None,
        }

        if not await has_permission(
            current_user, resource, action, context=context
        ):
            raise PermissionException(action=action, resource=resource)
        return current_user

    return permission_dependency


async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log
