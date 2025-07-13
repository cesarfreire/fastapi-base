from http import HTTPStatus

import pytest

from fastapi_base.schemas import GroupResponseSchema


@pytest.mark.asyncio
async def test_create_group_deve_criar_grupo_e_retornar_201(
    client, admin_token
):
    response = await client.post(
        '/groups/',
        json={
            'name': 'Grupo de teste',
            'description': 'Este é um grupo de teste',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 2,
        'name': 'Grupo de teste',
        'description': 'Este é um grupo de teste',
    }


@pytest.mark.asyncio
async def test_create_group_duplicado_deve_retornar_409(
    client, group, admin_token
):
    response = await client.post(
        '/groups/',
        json={
            'name': group.name,
            'description': 'Este é um grupo de teste',
        },
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Group name already exists'}


@pytest.mark.asyncio
async def test_read_groups_deve_retornar_lista_de_grupos(
    client, group, admin_token
):
    group_schema = GroupResponseSchema.model_validate(group).model_dump()
    response = await client.get(
        '/groups/', headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'groups': [
            {
                'id': 1,
                'name': 'Administradores',
                'description': 'Grupo de administradores',
            },
            group_schema,
        ]
    }


@pytest.mark.asyncio
async def test_read_group_deve_retornar_grupo_existente(
    client, group, admin_token
):
    response = await client.get(
        f'/groups/{group.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'name': group.name,
        'description': group.description,
        'id': group.id,
        'roles': [],
        'users': [],
    }


@pytest.mark.asyncio
async def test_read_group_deve_retornar_grupo_inexistente(client, admin_token):
    response = await client.get(
        '/groups/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_delete_group_deve_deletar_grupo_existente(
    client, group, admin_token
):
    response = await client.delete(
        f'/groups/{group.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': group.id,
        'name': group.name,
        'description': group.description,
    }


@pytest.mark.asyncio
async def test_delete_group_deve_retornar_404_para_grupo_inexistente(
    client, admin_token
):
    response = await client.delete(
        '/groups/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_update_group_deve_atualizar_grupo_existente(
    client, group, admin_token
):
    response = await client.put(
        f'/groups/{group.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'name': 'Grupo atualizado',
            'description': 'Descrição atualizada',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': group.id,
        'name': 'Grupo atualizado',
        'description': 'Descrição atualizada',
    }


@pytest.mark.asyncio
async def test_update_group_deve_retornar_404_para_grupo_inexistente(
    client, admin_token
):
    response = await client.put(
        '/groups/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'name': 'Grupo atualizado',
            'description': 'Descrição atualizada',
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_update_group_deve_retornar_409_para_nome_duplicado(
    client, group, admin_token
):
    response = await client.put(
        f'/groups/{group.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'name': 'Administradores',
            'description': 'Descrição atualizada',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Group name already exists'}


@pytest.mark.asyncio
async def test_add_user_to_group_deve_adicionar_usuario_ao_grupo(
    client, group, user, admin_token
):
    response = await client.post(
        f'/groups/{group.id}/users/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'User added to group successfully',
    }


@pytest.mark.asyncio
async def test_add_user_to_group_deve_retornar_404_para_grupo_inexistente(
    client, user, admin_token
):
    response = await client.post(
        '/groups/989656/users/1',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_add_user_to_group_deve_retornar_404_para_usuario_inexistente(
    client, group, admin_token
):
    response = await client.post(
        f'/groups/{group.id}/users/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


@pytest.mark.asyncio
async def test_add_user_to_group_deve_retornar_409_para_usuario_ja_no_grupo(
    client, group, user, admin_token
):
    response = await client.post(
        f'/groups/{group.id}/users/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'User added to group successfully',
    }

    # Tentar adicionar o mesmo usuário novamente
    response = await client.post(
        f'/groups/{group.id}/users/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'User already in group'}


@pytest.mark.asyncio
async def test_remove_user_from_group_deve_remover_usuario_do_grupo(
    client, group, user, admin_token
):
    # Primeiro, adiciona o usuário ao grupo
    await client.post(
        f'/groups/{group.id}/users/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    # Agora, remove o usuário do grupo
    response = await client.delete(
        f'/groups/{group.id}/users/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'User removed from group successfully'
    }


@pytest.mark.asyncio
async def test_remove_user_from_group_deve_retornar_404_para_grupo_inexistente(
    client, user, admin_token
):
    response = await client.delete(
        '/groups/989656/users/1',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_rm_user_from_group_deve_reto_404_para_usuario_inexistente(
    client, group, admin_token
):
    response = await client.delete(
        f'/groups/{group.id}/users/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found in group'}


@pytest.mark.asyncio
async def test_rm_user_from_group_deve_reto_404_para_usuario_nao_no_grupo(
    client, group, user, admin_token
):
    response = await client.delete(
        f'/groups/{group.id}/users/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found in group'}


@pytest.mark.asyncio
async def test_add_user_to_group_deve_retornar_403_para_usuario_nao_autorizado(
    client, group, user
):
    response = await client.post(
        f'/groups/{group.id}/users/{user.id}',
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


@pytest.mark.asyncio
async def test_add_role_to_group_deve_adicionar_role_ao_grupo(
    client, group, role, admin_token
):
    response = await client.post(
        f'/groups/{group.id}/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Role assigned to group successfully',
    }


@pytest.mark.asyncio
async def test_add_role_to_group_deve_retornar_404_para_grupo_inexistente(
    client, role, admin_token
):
    response = await client.post(
        '/groups/989656/roles/1',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_add_role_to_group_deve_retornar_404_para_role_inexistente(
    client, group, admin_token
):
    response = await client.post(
        f'/groups/{group.id}/roles/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found'}


@pytest.mark.asyncio
async def test_add_role_to_group_deve_retornar_409_para_role_ja_no_grupo(
    client, group, role, admin_token
):
    # Primeiro, adiciona a role ao grupo
    response = await client.post(
        f'/groups/{group.id}/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Role assigned to group successfully',
    }

    # Tentar adicionar a mesma role novamente
    response = await client.post(
        f'/groups/{group.id}/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Role already assigned to group'}


@pytest.mark.asyncio
async def test_remove_role_from_group_deve_remover_role_do_grupo(
    client, group, role, admin_token
):
    # Primeiro, adiciona a role ao grupo
    await client.post(
        f'/groups/{group.id}/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    # Agora, remove a role do grupo
    response = await client.delete(
        f'/groups/{group.id}/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Role removed from group successfully'
    }


@pytest.mark.asyncio
async def test_remove_role_from_group_deve_retornar_404_para_grupo_inexistente(
    client, role, admin_token
):
    response = await client.delete(
        '/groups/989656/roles/1',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Group not found'}


@pytest.mark.asyncio
async def test_remove_role_from_group_deve_retornar_404_para_role_inexistente(
    client, group, admin_token
):
    response = await client.delete(
        f'/groups/{group.id}/roles/989656',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found in group'}


@pytest.mark.asyncio
async def test_remove_role_from_group_deve_retornar_404_para_role_nao_no_grupo(
    client, group, role, admin_token
):
    response = await client.delete(
        f'/groups/{group.id}/roles/{role.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Role not found in group'}
