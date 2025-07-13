from http import HTTPStatus

import pytest

from fastapi_base.schemas import RoleResponseSchema


@pytest.mark.asyncio
async def test_create_role_deve_criar_role_e_retornar_201(client, admin_token):
    response = await client.post(
        '/roles/',
        json={
            'name': 'Função de teste',
            'description': 'Este é uma função de teste',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 2,
        'name': 'Função de teste',
        'description': 'Este é uma função de teste',
    }


@pytest.mark.asyncio
async def test_create_role_deve_retornar_409_para_role_existente(
    client, admin_token, role
):
    response = await client.post(
        '/roles/',
        json={
            'name': role.name,
            'description': 'Este é uma função de teste',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Role name already exists'}


@pytest.mark.asyncio
async def test_read_roles_deve_retornar_lista_de_roles(
    client, admin_token, role
):
    role_schema = RoleResponseSchema.model_validate(role).model_dump()
    response = await client.get(
        '/roles/', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'roles': [
            {
                'id': 1,
                'name': 'Administrador',
                'description': 'Função de administrador',
            },
            role_schema,
        ]
    }


@pytest.mark.asyncio
async def test_read_role_deve_retornar_role_existente(
    client, admin_token, role
):
    response = await client.get(
        f'/roles/{role.id}', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': role.id,
        'name': role.name,
        'description': role.description,
    }


@pytest.mark.asyncio
async def test_read_role_deve_retornar_404_para_role_nao_existente(
    client, admin_token
):
    response = await client.get(
        '/roles/999', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found'}


@pytest.mark.asyncio
async def test_delete_role_deve_deletar_role_existente(
    client, admin_token, role
):
    response = await client.delete(
        f'/roles/{role.id}', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': role.id,
        'name': role.name,
        'description': role.description,
    }


@pytest.mark.asyncio
async def test_delete_role_deve_retornar_404_para_role_nao_existente(
    client, admin_token
):
    response = await client.delete(
        '/roles/999', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found'}


@pytest.mark.asyncio
async def test_update_role_deve_atualizar_role_existente(
    client, admin_token, role
):
    response = await client.put(
        f'/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'name': 'Função atualizada',
            'description': 'Descrição atualizada',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': role.id,
        'name': 'Função atualizada',
        'description': 'Descrição atualizada',
    }


@pytest.mark.asyncio
async def test_update_role_deve_retornar_404_para_role_nao_existente(
    client, admin_token
):
    response = await client.put(
        '/roles/999',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'name': 'Função atualizada',
            'description': 'Descrição atualizada',
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found'}


@pytest.mark.asyncio
async def test_update_role_deve_retornar_409_para_nome_existente(
    client, admin_token, role
):
    response = await client.put(
        f'/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'name': 'Administrador',
            'description': 'Descrição atualizada',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Role name already exists'}
