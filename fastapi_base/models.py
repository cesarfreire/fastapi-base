from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    registry,
    relationship,
)


class Base(DeclarativeBase):
    pass


table_registry = registry()

user_roles = Table(
    'user_roles',
    table_registry.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
)

role_permissions = Table(
    'role_permissions',
    table_registry.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
    Column(
        'permission_id',
        Integer,
        ForeignKey('permissions.id', ondelete='CASCADE'),
    ),
)

user_permissions = Table(
    'user_permissions',
    table_registry.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column(
        'permission_id',
        Integer,
        ForeignKey('permissions.id', ondelete='CASCADE'),
    ),
)

user_groups = Table(
    'user_groups',
    table_registry.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE')),
)

group_roles = Table(
    'group_roles',
    table_registry.metadata,
    Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
)


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    roles: Mapped[List['Role']] = relationship(
        secondary=user_roles,
        back_populates='users',
        lazy='selectin',
        init=False,
    )
    direct_permissions: Mapped[List['Permission']] = relationship(
        secondary=user_permissions,
        back_populates='users',
        lazy='selectin',
        init=False,
    )
    groups: Mapped[List['Group']] = relationship(
        secondary=user_groups,
        back_populates='users',
        lazy='selectin',
        init=False,
    )
    audit_logs: Mapped[List['AuditLog']] = relationship(
        back_populates='user', lazy='selectin', init=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), init=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)


@table_registry.mapped_as_dataclass
class Role:
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    users: Mapped[List['User']] = relationship(
        secondary=user_roles, back_populates='roles', init=False
    )
    permissions: Mapped[List['Permission']] = relationship(
        secondary=role_permissions,
        back_populates='roles',
        lazy='selectin',
        init=False,
    )
    groups: Mapped[List['Group']] = relationship(
        secondary=group_roles,
        back_populates='roles',
        lazy='selectin',
        init=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), init=False
    )


@table_registry.mapped_as_dataclass
class Permission:
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))
    conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    roles: Mapped[List['Role']] = relationship(
        secondary=role_permissions,
        back_populates='permissions',
        lazy='selectin',
        init=False,
    )
    users: Mapped[List['User']] = relationship(
        secondary=user_permissions,
        back_populates='direct_permissions',
        lazy='selectin',
        init=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), init=False
    )

    __table_args__ = (
        {'sqlite_autoincrement': True},  # For SQLite, if used
    )


@table_registry.mapped_as_dataclass
class Group:
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    users: Mapped[List['User']] = relationship(
        secondary=user_groups,
        back_populates='groups',
        lazy='selectin',
        init=False,
    )
    roles: Mapped[List['Role']] = relationship(
        secondary=group_roles,
        back_populates='groups',
        lazy='selectin',
        init=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), init=False
    )


@table_registry.mapped_as_dataclass
class AuditLog:
    __tablename__ = 'audit_logs'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50))
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), init=False
    )

    user: Mapped[Optional['User']] = relationship(
        back_populates='audit_logs', lazy='selectin', init=False
    )


class TodoState(str, Enum):
    draft = 'draft'
    todo = 'todo'
    doing = 'doing'
    done = 'done'
    trash = 'trash'
