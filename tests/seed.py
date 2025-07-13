from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_base.models import Group, Permission, Role

# Lista de permissões
PERMISSIONS_TO_CREATE = [
    {
        "name": "user_create",
        "resource": "users",
        "action": "create",
        "description": "Criar usuários",
        "conditions": None,
    },
    {
        "name": "user_read",
        "resource": "users",
        "action": "read",
        "description": "Ler usuários",
        "conditions": None,
    },
    {
        "name": "user_update",
        "resource": "users",
        "action": "update",
        "description": "Atualizar usuários",
        "conditions": None,
    },
    {
        "name": "user_update_password",
        "resource": "users",
        "action": "update_password",
        "description": "Atualizar senha de usuários",
        "conditions": None,
    },
    {
        "name": "user_delete",
        "resource": "users",
        "action": "delete",
        "description": "Deletar usuários",
        "conditions": None,
    },
    {
        "name": "user_list",
        "resource": "users",
        "action": "list",
        "description": "Listar usuários",
        "conditions": None,
    },
    {
        "name": "role_create",
        "resource": "roles",
        "action": "create",
        "description": "Criar roles",
        "conditions": None,
    },
    {
        "name": "role_read",
        "resource": "roles",
        "action": "read",
        "description": "Ler roles",
        "conditions": None,
    },
    {
        "name": "role_update",
        "resource": "roles",
        "action": "update",
        "description": "Atualizar roles",
        "conditions": None,
    },
    {
        "name": "role_delete",
        "resource": "roles",
        "action": "delete",
        "description": "Deletar roles",
        "conditions": None,
    },
    {
        "name": "role_list",
        "resource": "roles",
        "action": "list",
        "description": "Listar roles",
        "conditions": None,
    },
    {
        "name": "group_create",
        "resource": "groups",
        "action": "create",
        "description": "Criar grupos",
        "conditions": None,
    },
    {
        "name": "group_read",
        "resource": "groups",
        "action": "read",
        "description": "Ler grupos",
        "conditions": None,
    },
    {
        "name": "group_update",
        "resource": "groups",
        "action": "update",
        "description": "Atualizar grupos",
        "conditions": None,
    },
    {
        "name": "group_delete",
        "resource": "groups",
        "action": "delete",
        "description": "Deletar grupos",
        "conditions": None,
    },
    {
        "name": "group_dadd",
        "resource": "groups",
        "action": "add_user",
        "description": "Adicionar usuário ao grupo",
        "conditions": None,
    },
    {
        "name": "group_remove",
        "resource": "groups",
        "action": "remove_user",
        "description": "Remover usuário do grupo",
        "conditions": None,
    },
    {
        "name": "group_list",
        "resource": "groups",
        "action": "list",
        "description": "Listar grupos",
        "conditions": None,
    },
    {
        "name": "group_assign_role",
        "resource": "groups",
        "action": "assign_role",
        "description": "Atribuir role ao grupo",
        "conditions": None,
    },
    {
        "name": "group_remove_role",
        "resource": "groups",
        "action": "remove_role",
        "description": "Remover role do grupo",
        "conditions": None,
    },
    {
        "name": "permission_create",
        "resource": "permissions",
        "action": "create",
        "description": "Criar permissões",
        "conditions": None,
    },
    {
        "name": "permission_read",
        "resource": "permissions",
        "action": "read",
        "description": "Ler permissões",
        "conditions": None,
    },
    {
        "name": "permission_update",
        "resource": "permissions",
        "action": "update",
        "description": "Atualizar permissões",
        "conditions": None,
    },
    {
        "name": "permission_delete",
        "resource": "permissions",
        "action": "delete",
        "description": "Deletar permissões",
        "conditions": None,
    },
    {
        "name": "permission_list",
        "resource": "permissions",
        "action": "list",
        "description": "Listar permissões",
        "conditions": None,
    },
    {
        "name": "permission_assign",
        "resource": "permissions",
        "action": "assign",
        "description": "Atribuir permissões",
        "conditions": None,
    },
]

# Lista de grupos
GROUPS_TO_CREATE = [
    {"name": "Administradores", "description": "Grupo de administradores"}
]

# Lista de roles
ROLES_TO_CREATE = [
    {
        "name": "Administrador",
        "description": "Função de administrador",
    }
]

# Associação de grupos e roles
GROUPS_ROLES_TO_CREATE = [
    {
        "group_name": "Administradores",
        "roles": ["Administrador"],
    }
]

# Associação de roles e permissões
# (Tudo para administrador, por enquanto)
ROLES_PERMISSIONS_TO_CREATE = [
    {
        "role_name": "Administrador",
        "permissions": [
            "user_create",
            "user_read",
            "user_update",
            "user_delete",
            "user_list",
            "role_create",
            "role_read",
            "role_update",
            "role_delete",
            "role_list",
            "group_create",
            "group_read",
            "group_update",
            "group_delete",
            "group_dadd",
            "group_remove",
            "group_list",
            "group_assign_role",
            "group_remove_role",
            "permission_create",
            "permission_read",
            "permission_update",
            "permission_delete",
            "permission_assign",
            "permission_list",
        ],
    }
]


async def seed_data_with_session(session: AsyncSession):
    """
    Popula o banco de dados usando uma sessão externa (ideal para testes).
    """
    permissions_map = {}
    for perm_data in PERMISSIONS_TO_CREATE:
        stmt = select(Permission).where(Permission.name == perm_data["name"])
        existing_permission = await session.scalar(stmt)
        if not existing_permission:
            new_permission = Permission(**perm_data)
            session.add(new_permission)
            permissions_map[perm_data["name"]] = new_permission
        else:
            permissions_map[existing_permission.name] = existing_permission

    groups_map = {}
    for group_data in GROUPS_TO_CREATE:
        stmt = select(Group).where(Group.name == group_data["name"])
        existing_group = await session.scalar(stmt)
        if not existing_group:
            new_group = Group(**group_data)
            session.add(new_group)
            groups_map[group_data["name"]] = new_group
        else:
            groups_map[existing_group.name] = existing_group

    roles_map = {}
    for role_data in ROLES_TO_CREATE:
        stmt = select(Role).where(Role.name == role_data["name"])
        existing_role = await session.scalar(stmt)
        if not existing_role:
            new_role = Role(**role_data)
            session.add(new_role)
            roles_map[role_data["name"]] = new_role
        else:
            roles_map[existing_role.name] = existing_role

    await session.flush()

    for group_name in groups_map:
        stmt = select(Group).options(selectinload(Group.roles)).where(Group.name == group_name)
        result = await session.execute(stmt)
        groups_map[group_name] = result.scalar_one()

    for role_name in roles_map:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == role_name)
        result = await session.execute(stmt)
        roles_map[role_name] = result.scalar_one()

    for group_role_data in GROUPS_ROLES_TO_CREATE:
        group = groups_map.get(group_role_data["group_name"])
        if group:
            for role_name in group_role_data["roles"]:
                role = roles_map.get(role_name)
                if role and role not in group.roles:
                    group.roles.append(role)

    for role_perm_data in ROLES_PERMISSIONS_TO_CREATE:
        role = roles_map.get(role_perm_data["role_name"])
        if role:
            for perm_name in role_perm_data["permissions"]:
                permission = permissions_map.get(perm_name)
                if permission and permission not in role.permissions:
                    role.permissions.append(permission)

    await session.commit()