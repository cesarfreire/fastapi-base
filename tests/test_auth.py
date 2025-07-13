from http import HTTPStatus

import pytest
from freezegun import freeze_time

from fastapi_base.security import create_access_token


@pytest.mark.asyncio
async def test_create_token_deve_retornar_token_para_usuario_existente(
    client, admin_user
):
    response = await client.post(
        '/auth/token',
        data={
            'username': admin_user.email,
            'password': admin_user.clean_password,
        },
    )

    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token


@pytest.mark.asyncio
async def test_get_current_user_nao_existente_deve_retornar_403(client):
    data = {'sub': 'test@test'}
    token = create_access_token(data)

    response = await client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_create_token_deve_retornar_403_para_usuario_inexistente(client):
    response = await client.post(
        '/auth/token',
        data={
            'username': 'test',
            'password': 'test',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


@pytest.mark.asyncio
async def test_create_token_deve_retornar_403_para_senha_incorreta(
    client, user
):
    response = await client.post(
        '/auth/token',
        data={
            'username': user.email,
            'password': 'wrong_password',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


@pytest.mark.asyncio
async def test_token_expirado_deve_retornar_403(client, user):
    with freeze_time('2025-07-01 12:00:00'):
        response = await client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2025-07-01 12:31:00'):
        response = await client.put(
            f'/users/{user.id}',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'username': 'wrongwrong',
                'email': 'wrong@wrong.com',
                'password': 'wrong',
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_refresh_token_deve_retornar_novo_token_valido(
    client, user, token
):
    response = await client.post(
        '/auth/refresh_token',
        headers={'Authorization': f'Bearer {token}'},
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'Bearer'


@pytest.mark.asyncio
async def test_token_expirado_deve_retornar_403_ao_renovar(client, user):
    with freeze_time('2025-07-01 12:00:00'):
        response = await client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2025-07-01 12:31:00'):
        response = await client.post(
            '/auth/refresh_token',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}
