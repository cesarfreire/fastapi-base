from datetime import datetime
from http import HTTPStatus

import pytest
from jwt import decode
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.models import User
from fastapi_base.security import create_access_token, has_permission


def test_jwt(settings):
    data = {'test': 'test'}
    token = create_access_token(data)

    decoded = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


@pytest.mark.asyncio
async def test_jwt_invalid_token(client):
    response = await client.delete(
        '/users/1', headers={'Authorization': 'Bearer invalid_token'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.asyncio
async def test_superuser_tem_acesso_total(admin_user):
    result = await has_permission(
        admin_user, resource='qualquer_coisa', action='qualquer_acao'
    )
    assert result is True


@pytest.mark.asyncio
async def test_permissao_direta_concedida(session, user, permission_factory):
    p_users_read = await permission_factory(resource='users', action='read')
    user.direct_permissions.append(p_users_read)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert await has_permission(user, resource='users', action='read') is True
    assert (
        await has_permission(user, resource='users', action='delete') is False
    )


@pytest.mark.asyncio
async def test_condicao_abac_falha_acesso_horario(
    session: AsyncSession, user: User, permission_factory
):
    p_conditional = await permission_factory(
        resource='reports',
        action='generate',
        conditions={'time_between': ['09:00', '17:00']},
    )
    user.direct_permissions.append(p_conditional)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    contexto_invalido = {
        'current_time': datetime.strptime('18:30', '%H:%M').time()
    }
    acesso_negado = await has_permission(
        user, resource='reports', action='generate', context=contexto_invalido
    )

    assert acesso_negado is False


@pytest.mark.asyncio
async def test_condicao_abac_falha_acesso_ip(
    session: AsyncSession, user: User, permission_factory
):
    p_conditional_ip = await permission_factory(
        resource='reports',
        action='generate',
        conditions={'ip_range': ['45.85.36.48']},
    )
    user.direct_permissions.append(p_conditional_ip)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    contexto_invalido = {'ip_address': '45.85.36.47'}
    acesso_negado = await has_permission(
        user, resource='reports', action='generate', context=contexto_invalido
    )

    assert acesso_negado is False


@pytest.mark.asyncio
async def test_condicao_abac_sucess_acesso_horario(
    session: AsyncSession, user: User, permission_factory
):
    p_conditional = await permission_factory(
        resource='reports',
        action='generate',
        conditions={'time_between': ['10:00', '17:00']},
    )
    user.direct_permissions.append(p_conditional)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    contexto_valido = {
        'current_time': datetime.strptime('15:30', '%H:%M').time()
    }
    acesso_concedido = await has_permission(
        user, resource='reports', action='generate', context=contexto_valido
    )

    assert acesso_concedido is True


@pytest.mark.asyncio
async def test_condicao_abac_sucesso_acesso_ip(
    session: AsyncSession, user: User, permission_factory
):
    p_conditional_ip = await permission_factory(
        resource='reports',
        action='generate',
        conditions={'ip_range': ['45.85.36.48']},
    )
    user.direct_permissions.append(p_conditional_ip)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    contexto_valido = {'ip_address': '45.85.36.48'}
    acesso_concedido = await has_permission(
        user, resource='reports', action='generate', context=contexto_valido
    )

    assert acesso_concedido is True


@pytest.mark.asyncio
async def test_permissao_via_role_concedida(
    session, user, permission_factory, role
):
    p_role = await permission_factory(resource='reports', action='generate')
    role.permissions.append(p_role)
    user.roles.append(role)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert (
        await has_permission(user, resource='reports', action='generate')
        is True
    )
    assert await has_permission(user, resource='users', action='list') is False


@pytest.mark.asyncio
async def test_permissao_via_group_concedida(
    session, user, permission_factory, group, role
):
    p_group = await permission_factory(resource='reports', action='generate')
    role.permissions.append(p_group)
    group.roles.append(role)
    user.groups.append(group)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert (
        await has_permission(user, resource='reports', action='generate')
        is True
    )
    assert await has_permission(user, resource='users', action='list') is False
