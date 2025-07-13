from http import HTTPStatus

from fastapi import HTTPException


class CredentialsException(HTTPException):
    def __init__(self, detail: str = 'Could not validate credentials'):
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'},
        )


class PermissionException(HTTPException):
    def __init__(
        self,
        action: str,
        resource: str,
        detail: str = 'You do not have permission to perform this action',
    ):
        super().__init__(
            status_code=HTTPStatus.FORBIDDEN,
            detail=f'You do not have permission to '
            f'perform this action: {action} on {resource}',
        )


class UserNotActiveException(HTTPException):
    def __init__(self, detail: str = 'User is not active'):
        super().__init__(
            status_code=HTTPStatus.FORBIDDEN,
            detail=detail,
        )
