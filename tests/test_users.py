from http import HTTPStatus

import pytest

from fastapi_base.schemas import UserResponseSchema
from fastapi_base.security import create_access_token


@pytest.mark.asyncio
async def test_create_user_deve_criar_usuario_e_retornar_201(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'Secret@123',
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'username': 'alice',
        'email': 'alice@example.com',
        'is_active': True,
    }


@pytest.mark.asyncio
async def test_create_user_deve_retornar_422_para_dados_invalidos(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'invalid-email',
            'password': 'Secret@123',
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'ctx': {'reason': 'An email address must have an @-sign.'},
                'loc': ['body', 'email'],
                'msg': 'value is not a valid email address: '
                'An email address must have an @-sign.',
                'type': 'value_error',
                'input': 'invalid-email',
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_user_deve_retornar_422_para_senha_curta(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'my-test-user',
            'email': 'alice@example.com',
            'password': '123',
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'password'],
                'msg': 'Value error, Password must be at least 8 characters',
                'type': 'value_error',
                'input': '123',
                'ctx': {'error': {}},
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_user_deve_retornar_422_para_senha_sem_numeros(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'my-test-user',
            'email': 'alice@example.com',
            'password': 'abcdefghij',
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'password'],
                'msg': 'Value error, Password must contain at least one digit',
                'type': 'value_error',
                'input': 'abcdefghij',
                'ctx': {'error': {}},
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_user_deve_retornar_422_para_senha_so_maiuscula(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'my-test-user',
            'email': 'alice@example.com',
            'password': 'ABCDEFGHIJKLMNOP@123',
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'password'],
                'msg': 'Value error, Password must contain at '
                'least one lowercase letter',
                'type': 'value_error',
                'input': 'ABCDEFGHIJKLMNOP@123',
                'ctx': {'error': {}},
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_user_deve_reto_422_para_senha_sem_maiuscula(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'my-test-user',
            'email': 'alice@example.com',
            'password': 'abcdefg123@',
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'password'],
                'msg': 'Value error, Password must contain at '
                'least one uppercase letter',
                'type': 'value_error',
                'input': 'abcdefg123@',
                'ctx': {'error': {}},
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_user_deve_retornar_422_para_senha_sem_especial(client):
    response = await client.post(
        '/users/',
        json={
            'username': 'my-test-user',
            'email': 'alice@example.com',
            'password': 'ABCdefg123',
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'password'],
                'msg': 'Value error, Password must contain at least '
                'one special character',
                'type': 'value_error',
                'input': 'ABCdefg123',
                'ctx': {'error': {}},
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_user_deve_retornar_409_para_usuario_existente(
    client, user
):
    response = await client.post(
        '/users/',
        json={
            'username': user.username,
            'email': 'alice@example.com',
            'password': 'Secret@123',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username or email already exists'}


@pytest.mark.asyncio
async def test_create_user_deve_retornar_409_para_email_existente(
    client, user
):
    response = await client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': user.email,
            'password': 'Secret@123',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username or email already exists'}


@pytest.mark.asyncio
async def test_read_users_deve_retornar_lista_de_usuarios(
    client, admin_user, admin_token
):
    user_schema = UserResponseSchema.model_validate(admin_user).model_dump()
    response = await client.get(
        '/users/', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


@pytest.mark.asyncio
async def test_read_user_deve_retornar_usuario_existente(
    client, admin_user, admin_token
):
    response = await client.get(
        f'/users/{admin_user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': admin_user.username,
        'email': admin_user.email,
        'id': admin_user.id,
        'is_active': admin_user.is_active,
        'groups': [],
        'roles': [],
    }


@pytest.mark.asyncio
async def test_read_user_deve_retornar_404_para_usuario_inexistente(
    client, admin_user, admin_token
):
    response = await client.get(
        '/users/999',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


@pytest.mark.asyncio
async def test_update_user_deve_atualizar_usuario_existente(
    client, admin_user, admin_token
):
    response = await client.put(
        '/users/1',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'new_secret@123$',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': 1,
        'is_active': True,
    }


@pytest.mark.asyncio
async def test_update_user_deve_retornar_404_para_usuario_inexistente(
    client, admin_user, other_admin_user, admin_token
):
    response_update = await client.put(
        '/users/9999',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'username': other_admin_user.username,
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response_update.status_code == HTTPStatus.NOT_FOUND
    assert response_update.json() == {'detail': 'User not found'}


@pytest.mark.asyncio
async def test_update_user_deve_retornar_409_para_username_em_uso(
    client, admin_user, other_admin_user, admin_token
):
    response_update = await client.put(
        f'/users/{admin_user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'username': other_admin_user.username,
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        'detail': 'Username or email already exists'
    }


# Delete
@pytest.mark.asyncio
async def test_delete_user_deve_deletar_usuario_existente(
    client, admin_user, admin_token
):
    response = await client.delete(
        f'/users/{admin_user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted successfully'}


@pytest.mark.asyncio
async def test_delete_user_deve_retornar_404_usuario_inexistente(
    client, admin_token
):
    response = await client.delete(
        '/users/999999',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


@pytest.mark.asyncio
async def test_get_current_user_nao_encontrado_deve_retornar_403(client):
    data = {'no-email': 'test'}
    token = create_access_token(data)

    response = await client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_user_list_deve_retornar_403_para_usuario_sem_permissao(
    client, user, token
):
    response = await client.get(
        '/users/',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {
        'detail': 'You do not have permission to '
        'perform this action: list on users'
    }


@pytest.mark.asyncio
async def test_user_inactive_deve_retornar_403(
    client, inactive_token, inactive_user
):
    response = await client.get(
        f'/users/{inactive_user.id}',
        headers={'Authorization': f'Bearer {inactive_token}'},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'User is not active'}
