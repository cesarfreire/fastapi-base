from http import HTTPStatus

import pytest
from sqlalchemy import select

from fastapi_base.models import Permission


@pytest.mark.asyncio
async def test_create_permission_deve_criar_permission_e_retornar_201(
    client, admin_token
):
    response = await client.post(
        '/permissions/',
        json={
            'name': 'Permissão de teste',
            'description': 'Esta é uma permissão de teste',
            'resource': 'permissions',
            'action': 'create',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 27,
        'name': 'Permissão de teste',
        'description': 'Esta é uma permissão de teste',
        'resource': 'permissions',
        'action': 'create',
        'conditions': None,
    }


@pytest.mark.asyncio
async def test_create_permission_deve_retornar_409_para_permission_existente(
    client, admin_token, permission
):
    response = await client.post(
        '/permissions/',
        json={
            'name': permission.name,
            'description': 'Esta é uma permissão de teste',
            'resource': 'permissions',
            'action': permission.action,
            'conditions': permission.conditions,
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        'detail': 'Permission with this resource and action already exists'
    }


@pytest.mark.asyncio
async def test_read_permissions_deve_retornar_lista_de_permissions(
    client, admin_token, session
):
    result = await session.execute(select(Permission))
    db_permissions = result.scalars().all()
    expected_permission_names = {p.name for p in db_permissions}

    response = await client.get(
        '/permissions/', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.OK
    response_data = response.json()['permissions']

    returned_names = {perm['name'] for perm in response_data}
    assert expected_permission_names == returned_names


@pytest.mark.asyncio
async def test_read_permission_deve_retornar_permission_existente(
    client, admin_token, permission
):
    response = await client.get(
        f'/permissions/{permission.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': permission.id,
        'name': permission.name,
        'description': permission.description,
        'resource': permission.resource,
        'action': permission.action,
        'conditions': permission.conditions,
    }


@pytest.mark.asyncio
async def test_read_permission_nao_existente_deve_retornar_404(
    client, admin_token
):
    response = await client.get(
        '/permissions/9999', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Permission not found'}


@pytest.mark.asyncio
async def test_update_permission_deve_atualizar_permission_existente(
    client, admin_token, permission
):
    response = await client.put(
        f'/permissions/{permission.id}',
        json={
            'name': 'Permissão atualizada',
            'description': 'Descrição atualizada',
            'resource': permission.resource,
            'action': permission.action,
            'conditions': permission.conditions,
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': permission.id,
        'name': 'Permissão atualizada',
        'description': 'Descrição atualizada',
        'resource': permission.resource,
        'action': permission.action,
        'conditions': permission.conditions,
    }


@pytest.mark.asyncio
async def test_update_permission_nao_existente_deve_retornar_404(
    client, admin_token
):
    response = await client.put(
        '/permissions/9999',
        json={
            'name': 'Permissão atualizada',
            'description': 'Descrição atualizada',
            'resource': 'permissions',
            'action': 'update',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Permission not found'}


@pytest.mark.asyncio
async def test_update_permission_deve_retornar_409_para_permission_existente(
    client, admin_token, permission, other_permission
):
    response = await client.put(
        f'/permissions/{permission.id}',
        json={
            'name': other_permission.name,
            'description': other_permission.description,
            'resource': other_permission.resource,
            'action': other_permission.action,
            'conditions': other_permission.conditions,
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        'detail': 'Permission with this resource and action already exists'
    }


@pytest.mark.asyncio
async def test_delete_permission_deve_remover_permission_existente(
    client, admin_token, permission
):
    response = await client.delete(
        f'/permissions/{permission.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Permission deleted successfully'}


@pytest.mark.asyncio
async def test_delete_permission_nao_existente_deve_retornar_404(
    client, admin_token
):
    response = await client.delete(
        '/permissions/9999', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Permission not found'}


@pytest.mark.asyncio
async def test_assign_permission_to_role_deve_atribuir_permission_a_role(
    client, admin_token, permission, role
):
    response = await client.post(
        f'/permissions/{permission.id}/assign-to-role/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': f"Permission '{permission.name}' assigned "
        f"to role '{role.name}'"
    }


@pytest.mark.asyncio
async def test_assign_permission_to_role_nao_existente_deve_retornar_404(
    client, admin_token, permission
):
    response = await client.post(
        '/permissions/9999/assign-to-role/1',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Permission not found'}


@pytest.mark.asyncio
async def test_assign_permission_to_role_role_nao_existente_deve_retornar_404(
    client, admin_token, permission
):
    response = await client.post(
        f'/permissions/{permission.id}/assign-to-role/9999',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found'}
