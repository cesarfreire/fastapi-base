from dataclasses import asdict

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.models import User


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession, mock_db_time):
    with mock_db_time(model=User) as time:
        new_user = User(
            username='alice', password='secret', email='teste@test'
        )
        session.add(new_user)
        await session.commit()

    user = await session.scalar(select(User).where(User.username == 'alice'))

    assert asdict(user) == {
        'id': 1,
        'username': 'alice',
        'email': 'teste@test',
        'password': 'secret',
        'created_at': time,
        'updated_at': time,
        'audit_logs': [],
        'direct_permissions': [],
        'groups': [],
        'roles': [],
        'is_active': True,
        'is_superuser': False,
    }


# @pytest.mark.asyncio
# async def test_create_todo(session, user, mock_db_time):
#     with mock_db_time(model=Todo) as time:
#         todo = Todo(
#             title='Test Todo',
#             description='This is a test todo item.',
#             user_id=user.id,
#             state='draft',
#         )
#
#         session.add(todo)
#         await session.commit()
#
#     todo = await session.scalar(select(Todo))
#
#     assert asdict(todo) == {
#         'title': 'Test Todo',
#         'description': 'This is a test todo item.',
#         'state': 'draft',
#         'user_id': user.id,
#         'id': 1,
#         'created_at': time,
#         'updated_at': time,
#     }
#
#
# @pytest.mark.asyncio
# async def test_user_todo_relationship(session, user: User):
#     todo = Todo(
#         title='Test Todo',
#         description='Test Desc',
#         state='draft',
#         user_id=user.id,
#     )
#
#     session.add(todo)
#     await session.commit()
#     await session.refresh(user)
#
#     user = await session.scalar(select(User).where(User.id == user.id))
#
#     assert user.todos == [todo]
