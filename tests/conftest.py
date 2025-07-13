from contextlib import contextmanager
from datetime import datetime
from typing import Awaitable, Callable

import factory
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from fastapi_base.app import app
from fastapi_base.database import get_session
from fastapi_base.models import (
    Group,
    Permission,
    Role,
    User,
    table_registry,
)
from fastapi_base.security import get_password_hash
from fastapi_base.settings import Settings
from tests.seed import seed_data_with_session

# Lista de permissões
PERMISSIONS_TO_CREATE = [
    {
        'name': 'user_create',
        'resource': 'users',
        'action': 'create',
        'description': 'Criar usuários',
    },
    {
        'name': 'user_read',
        'resource': 'users',
        'action': 'read',
        'description': 'Ler usuários',
    },
    {
        'name': 'user_update',
        'resource': 'users',
        'action': 'update',
        'description': 'Atualizar usuários',
    },
    {
        'name': 'user_delete',
        'resource': 'users',
        'action': 'delete',
        'description': 'Deletar usuários',
    },
    {
        'name': 'user_list',
        'resource': 'users',
        'action': 'list',
        'description': 'Listar usuários',
    },
    {
        'name': 'role_create',
        'resource': 'roles',
        'action': 'create',
        'description': 'Criar roles',
    },
    {
        'name': 'role_read',
        'resource': 'roles',
        'action': 'read',
        'description': 'Ler roles',
    },
    {
        'name': 'role_update',
        'resource': 'roles',
        'action': 'update',
        'description': 'Atualizar roles',
    },
    {
        'name': 'role_delete',
        'resource': 'roles',
        'action': 'delete',
        'description': 'Deletar roles',
    },
    {
        'name': 'role_list',
        'resource': 'roles',
        'action': 'list',
        'description': 'Listar roles',
    },
    {
        'name': 'group_create',
        'resource': 'groups',
        'action': 'create',
        'description': 'Criar grupos',
    },
    {
        'name': 'group_read',
        'resource': 'groups',
        'action': 'read',
        'description': 'Ler grupos',
    },
    {
        'name': 'group_update',
        'resource': 'groups',
        'action': 'update',
        'description': 'Atualizar grupos',
    },
    {
        'name': 'group_delete',
        'resource': 'groups',
        'action': 'delete',
        'description': 'Deletar grupos',
    },
    {
        'name': 'group_dadd',
        'resource': 'groups',
        'action': 'add_user',
        'description': 'Adicionar usuário ao grupo',
    },
    {
        'name': 'group_remove',
        'resource': 'groups',
        'action': 'remove_user',
        'description': 'Remover usuário do grupo',
    },
    {
        'name': 'group_list',
        'resource': 'groups',
        'action': 'list',
        'description': 'Listar grupos',
    },
    {
        'name': 'group_assign_role',
        'resource': 'groups',
        'action': 'assign_role',
        'description': 'Atribuir role ao grupo',
    },
    {
        'name': 'group_remove_role',
        'resource': 'groups',
        'action': 'remove_role',
        'description': 'Remover role do grupo',
    },
    {
        'name': 'permission_create',
        'resource': 'permissions',
        'action': 'create',
        'description': 'Criar permissões',
    },
    {
        'name': 'permission_read',
        'resource': 'permissions',
        'action': 'read',
        'description': 'Ler permissões',
    },
    {
        'name': 'permission_update',
        'resource': 'permissions',
        'action': 'update',
        'description': 'Atualizar permissões',
    },
    {
        'name': 'permission_delete',
        'resource': 'permissions',
        'action': 'delete',
        'description': 'Deletar permissões',
    },
    {
        'name': 'permission_list',
        'resource': 'permissions',
        'action': 'list',
        'description': 'Listar permissões',
    },
    {
        'name': 'permission_assign',
        'resource': 'permissions',
        'action': 'assign',
        'description': 'Atribuir permissões',
    },
]

# Lista de grupos
GROUPS_TO_CREATE = [
    {'name': 'Administradores', 'description': 'Grupo de administradores'}
]

# Lista de roles
ROLES_TO_CREATE = [
    {
        'name': 'Administrador',
        'description': 'Função de administrador',
    }
]

# Associação de grupos e roles
GROUPS_ROLES_TO_CREATE = [
    {
        'group_name': 'Administradores',
        'roles': ['Administrador'],
    }
]

# Associação de roles e permissões
# (Tudo para administrador, por enquanto)
ROLES_PERMISSIONS_TO_CREATE = [
    {
        'role_name': 'Administrador',
        'permissions': [
            'user_create',
            'user_read',
            'user_update',
            'user_delete',
            'user_list',
            'role_create',
            'role_read',
            'role_update',
            'role_delete',
            'role_list',
            'group_create',
            'group_read',
            'group_update',
            'group_delete',
            'group_dadd',
            'group_remove',
            'group_list',
            'group_assign_role',
            'group_remove_role',
            'permission_create',
            'permission_read',
            'permission_update',
            'permission_delete',
            'permission_assign',
            'permission_list',
        ],
    }
]

# Lista de grupos
GROUPS_TO_CREATE = [
    {'name': 'Administradores', 'description': 'Grupo de administradores'}
]

# Lista de roles
ROLES_TO_CREATE = [
    {
        'name': 'Administrador',
        'description': 'Função de administrador',
    }
]

# Associação de grupos e roles
GROUPS_ROLES_TO_CREATE = [
    {
        'group_name': 'Administradores',
        'roles': ['Administrador'],
    }
]

# Associação de roles e permissões
# (Tudo para administrador, por enquanto)
ROLES_PERMISSIONS_TO_CREATE = [
    {
        'role_name': 'Administrador',
        'permissions': [
            'user_create',
            'user_read',
            'user_update',
            'user_delete',
            'user_list',
            'role_create',
            'role_read',
            'role_update',
            'role_delete',
            'role_list',
            'group_create',
            'group_read',
            'group_update',
            'group_delete',
            'group_dadd',
            'group_remove',
            'group_list',
            'group_assign_role',
            'group_remove_role',
            'permission_create',
            'permission_read',
            'permission_update',
            'permission_delete',
            'permission_assign',
            'permission_list',
        ],
    }
]


class PermissionFactory(factory.Factory):
    class Meta:
        model = Permission

    name = factory.Sequence(lambda n: f'PermissionTest-{n}')
    resource = factory.LazyAttribute(lambda obj: obj.name.lower())
    action = factory.LazyAttribute(
        lambda obj: 'create' if 'create' in obj.name else 'read'
    )
    description = factory.LazyAttribute(
        lambda obj: f'This is the description from permission {obj.name}'
    )
    conditions = factory.LazyAttribute(lambda obj: None)


class RoleFactory(factory.Factory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f'RoleTest-{n}')
    description = factory.LazyAttribute(
        lambda obj: f'This is the description from role {obj.name}'
    )


class GroupFactory(factory.Factory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f'GroupTest-{n}')
    description = factory.LazyAttribute(
        lambda obj: f'This is the description from group {obj.name}'
    )


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyAttribute(lambda obj: f'{obj.username}@Secret@123')


@pytest.fixture(scope='session')
def engine():
    with PostgresContainer('postgres:16', driver='psycopg') as postgres:
        _engine = create_async_engine(postgres.get_connection_url())
        yield _engine


@pytest.fixture
def settings():
    """
    Fixture to provide application settings for testing.
    This can be used to override settings in tests if needed.
    """
    return Settings()


@pytest_asyncio.fixture
async def token(client: AsyncClient, user):
    """
    Fixture to create a JWT token for the user created in the `user` fixture.
    This token will be used in tests that require authentication.
    """
    response = await client.post(
        '/auth/token',
        data={
            'username': user.email,
            'password': user.clean_password,
        },
    )
    return response.json()['access_token']


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user):
    """
    Fixture to create a JWT token for the user created in the `user` fixture.
    This token will be used in tests that require authentication.
    """
    response = await client.post(
        '/auth/token',
        data={
            'username': admin_user.email,
            'password': admin_user.clean_password,
        },
    )
    return response.json()['access_token']


@pytest_asyncio.fixture
async def inactive_token(client: AsyncClient, inactive_user):
    """
    Fixture to create a JWT token for the inactive user
    created in the `inactive_user` fixture.
    This token will be used in tests that require authentication
    for an inactive user.
    """
    response = await client.post(
        '/auth/token',
        data={
            'username': inactive_user.email,
            'password': inactive_user.clean_password,
        },
    )
    return response.json()['access_token']


@pytest_asyncio.fixture
def permission_factory(
    session: AsyncSession,
) -> Callable[..., Awaitable[Permission]]:
    """
    Fixture que retorna uma "fábrica" assíncrona para criar permissões
    customizadas sob demanda nos testes.
    """

    async def _create_permission(**kwargs) -> Permission:
        """
        Função interna que cria, salva e retorna uma permissão.
        Aceita kwargs para sobrescrever os atributos padrão da factory.
        """
        # Cria a permissão usando a factory_boy, passando as customizações
        permission_obj = PermissionFactory(**kwargs)

        session.add(permission_obj)
        await session.commit()
        await session.refresh(permission_obj)

        return permission_obj

    return _create_permission


@pytest_asyncio.fixture
async def permission(session: AsyncSession):
    """
    Fixture to create a permission in the database for testing purposes.
    This permission will be used in tests that require a permission
    to be present.
    """
    permission = PermissionFactory()
    session.add(permission)
    await session.commit()
    await session.refresh(permission)

    return permission


@pytest_asyncio.fixture
async def other_permission(session: AsyncSession):
    """
    Fixture to create a permission in the database for testing purposes.
    This permission will be used in tests that require a permission
    to be present.
    """
    other_permission = PermissionFactory()
    session.add(other_permission)
    await session.commit()
    await session.refresh(other_permission)

    return other_permission


@pytest_asyncio.fixture
async def role(session: AsyncSession):
    """
    Fixture to create a role in the database for testing purposes.
    This role will be used in tests that require a role to be present.
    """
    role = RoleFactory()
    session.add(role)
    await session.commit()
    await session.refresh(role)

    return role


@pytest_asyncio.fixture
async def group(session: AsyncSession):
    """
    Fixture to create a group in the database for testing purposes.
    This group will be used in tests that require a group to be present.
    """
    group = GroupFactory()
    session.add(group)
    await session.commit()
    await session.refresh(group)

    return group


@pytest_asyncio.fixture
async def user(session: AsyncSession):
    """
    Fixture to create a user in the database for testing purposes.
    This user will be used in tests that require a user to be present.
    """
    password = 'Secret@123'
    user = UserFactory(password=get_password_hash(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password  # Store the plain password for tests

    return user


@pytest_asyncio.fixture
async def other_user(session):
    password = 'Secret@123'
    other_user = UserFactory(password=get_password_hash(password))

    session.add(other_user)
    await session.commit()
    await session.refresh(other_user)

    other_user.clean_password = password

    return other_user


@pytest_asyncio.fixture
async def inactive_user(session):
    password = 'Secret@123'
    inactive_user = UserFactory(
        password=get_password_hash(password), is_active=False
    )

    session.add(inactive_user)
    await session.commit()
    await session.refresh(inactive_user)

    inactive_user.clean_password = password

    return inactive_user


@pytest_asyncio.fixture
async def admin_user(session):
    password = 'Admin@123'
    admin_user = UserFactory(
        password=get_password_hash(password),
        is_superuser=True,
    )
    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)

    admin_user.clean_password = password
    return admin_user


@pytest_asyncio.fixture
async def other_admin_user(session):
    password = 'Admin@123'
    other_admin_user = UserFactory(
        password=get_password_hash(password),
        is_superuser=True,
    )
    session.add(other_admin_user)
    await session.commit()
    await session.refresh(other_admin_user)

    other_admin_user.clean_password = password
    return other_admin_user


@pytest_asyncio.fixture
async def client(session):
    """
    Fixture to create a TestClient for the FastAPI application.
    This allows us to use the client in our tests without needing to
    instantiate it multiple times.
    """

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        await seed_data_with_session(session)
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@pytest.fixture
def mock_db_time():
    """
    Fixture to mock the database time for testing purposes.
    It sets a fixed time for the `created_at` field in the User model.
    """
    return _mock_db_time


@contextmanager
def _mock_db_time(*, model, time=datetime(2024, 1, 1)):
    def fake_time_hook(mapper, connection, target):
        if hasattr(target, 'created_at'):
            target.created_at = time

        if hasattr(target, 'updated_at'):
            target.updated_at = time

    event.listen(model, 'before_insert', fake_time_hook)
    yield time
    event.remove(model, 'before_insert', fake_time_hook)


async def populate_database(session: AsyncSession):
    """
    Função reutilizável para popular o banco de dados com dados iniciais.
    Recebe a sessão como argumento e faz um único commit no final.
    """
    # --- Carregar ou Criar Permissões ---
    permissions_map = {}
    for perm_data in PERMISSIONS_TO_CREATE:
        stmt = select(Permission).where(Permission.name == perm_data['name'])
        existing_permission = await session.scalar(stmt)
        if not existing_permission:
            new_permission = Permission(**perm_data)
            session.add(new_permission)
            permissions_map[perm_data['name']] = new_permission
        else:
            permissions_map[existing_permission.name] = existing_permission

    # --- Carregar ou Criar Grupos ---
    groups_map = {}
    for group_data in GROUPS_TO_CREATE:
        stmt = select(Group).where(Group.name == group_data['name'])
        existing_group = await session.scalar(stmt)
        if not existing_group:
            new_group = Group(**group_data)
            session.add(new_group)
            groups_map[group_data['name']] = new_group
        else:
            groups_map[existing_group.name] = existing_group

    # --- Carregar ou Criar Roles ---
    roles_map = {}
    for role_data in ROLES_TO_CREATE:
        stmt = select(Role).where(Role.name == role_data['name'])
        existing_role = await session.scalar(stmt)
        if not existing_role:
            new_role = Role(**role_data)
            session.add(new_role)
            roles_map[role_data['name']] = new_role
        else:
            roles_map[existing_role.name] = existing_role

    # Flush para garantir que os objetos
    # recém-criados estejam prontos para associação
    await session.flush()

    # --- Associar Grupos e Roles ---
    for group_role_data in GROUPS_ROLES_TO_CREATE:
        group = groups_map.get(group_role_data['group_name'])
        if group:
            for role_name in group_role_data['roles']:
                role = roles_map.get(role_name)
                if role and role not in group.roles:
                    group.roles.append(role)

    # --- Associar Roles e Permissões ---
    for role_perm_data in ROLES_PERMISSIONS_TO_CREATE:
        role = roles_map.get(role_perm_data['role_name'])
        if role:
            for perm_name in role_perm_data['permissions']:
                permission = permissions_map.get(perm_name)
                if permission and permission not in role.permissions:
                    role.permissions.append(permission)

    # Salva todas as alterações de uma vez no final
    await session.commit()
