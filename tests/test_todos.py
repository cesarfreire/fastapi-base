# import factory.fuzzy
#
# from fastapi_base.models import TodoState
#

# class TodoFactory(factory.Factory):
#     class Meta:
#         model = Todo
#
#     title = factory.Faker('text')
#     description = factory.Faker('text')
#     state = factory.fuzzy.FuzzyChoice(TodoState)
#     user_id = 1


# def test_create_todo_deve_retornar_201(client, token, mock_db_time):
#     with mock_db_time(model=Todo) as time:
#         response = client.post(
#             '/todos',
#             headers={'Authorization': f'Bearer {token}'},
#             json={
#                 'title': 'Test todo',
#                 'description': 'Test todo description',
#                 'state': 'draft',
#             },
#         )
#     assert response.status_code == HTTPStatus.CREATED
#     assert response.json() == {
#         'id': 1,
#         'title': 'Test todo',
#         'description': 'Test todo description',
#         'state': 'draft',
#         'created_at': time.isoformat(),
#         'updated_at': time.isoformat(),
#     }
#
#
# @pytest.mark.asyncio
# async def test_list_todos_deve_retornar_todos_campos_esperados(
#     session, client, user, token, mock_db_time
# ):
#     with mock_db_time(model=Todo) as time:
#         todo = TodoFactory.create(user_id=user.id)
#         session.add(todo)
#         await session.commit()
#
#     await session.refresh(todo)
#     response = client.get(
#         '/todos',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert response.json()['todos'] == [
#         {
#             'created_at': time.isoformat(),
#             'updated_at': time.isoformat(),
#             'description': todo.description,
#             'id': todo.id,
#             'state': todo.state,
#             'title': todo.title,
#         }
#     ]
#
#
# @pytest.mark.asyncio
# async def test_list_todos_deve_retornar_lista_5_todos(
#     session, client, user, token
# ):
#     expected_todos = 5
#     session.add_all(TodoFactory.create_batch(5, user_id=user.id))
#     await session.commit()
#
#     response = client.get(
#         '/todos',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert len(response.json()['todos']) == expected_todos
#
#
# @pytest.mark.asyncio
# async def test_list_todos_paginacao_deve_retornar_2_todos(
#     session, user, client, token
# ):
#     expected_todos = 2
#     session.add_all(TodoFactory.create_batch(5, user_id=user.id))
#     await session.commit()
#
#     response = client.get(
#         '/todos/?offset=1&limit=2',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert len(response.json()['todos']) == expected_todos
#
#
# @pytest.mark.asyncio
# async def test_list_todos_filtro_titulo_deve_retornar_5_todos(
#     session, user, client, token
# ):
#     expected_todos = 5
#     session.add_all(
#         TodoFactory.create_batch(5, user_id=user.id, title='Test todo 1')
#     )
#     await session.commit()
#
#     response = client.get(
#         '/todos/?title=Test todo 1',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert len(response.json()['todos']) == expected_todos
#
#
# @pytest.mark.asyncio
# async def test_list_todos_filtro_descricao_deve_retornar_5_todos(
#     session, user, client, token
# ):
#     expected_todos = 5
#     session.add_all(
#         TodoFactory.create_batch(
#           5, user_id=user.id, description='description'
#          )
#     )
#     await session.commit()
#
#     response = client.get(
#         '/todos/?description=desc',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert len(response.json()['todos']) == expected_todos
#
#
# @pytest.mark.asyncio
# async def test_list_todos_filtro_estado_deve_retornar_5_todos(
#     session, user, client, token
# ):
#     expected_todos = 5
#     session.add_all(
#         TodoFactory.create_batch(5, user_id=user.id, state=TodoState.draft)
#     )
#     await session.commit()
#
#     response = client.get(
#         '/todos/?state=draft',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert len(response.json()['todos']) == expected_todos
#
#
# @pytest.mark.asyncio
# async def test_list_todos_filtros_combinados_devem_retornar_5_todos(
#     session, user, client, token
# ):
#     expected_todos = 5
#     session.add_all(
#         TodoFactory.create_batch(
#             5,
#             user_id=user.id,
#             title='Test todo combined',
#             description='combined description',
#             state=TodoState.done,
#         )
#     )
#
#     session.add_all(
#         TodoFactory.create_batch(
#             3,
#             user_id=user.id,
#             title='Other title',
#             description='other description',
#             state=TodoState.todo,
#         )
#     )
#     await session.commit()
#
#     response = client.get(
#         '/todos/?title=Test todo combined&description=combined&state=done',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert len(response.json()['todos']) == expected_todos
#
#
# def test_patch_todo_inexistente_deve_retornar_404(client, token):
#     response = client.patch(
#         '/todos/10',
#         json={},
#         headers={'Authorization': f'Bearer {token}'},
#     )
#     assert response.status_code == HTTPStatus.NOT_FOUND
#     assert response.json() == {'detail': 'Todo not found'}
#
#
# @pytest.mark.asyncio
# async def test_patch_todo_deve_retornar_200(session, client, user, token):
#     todo = TodoFactory(user_id=user.id)
#
#     session.add(todo)
#     await session.commit()
#
#     response = client.patch(
#         f'/todos/{todo.id}',
#         json={'title': 'teste!'},
#         headers={'Authorization': f'Bearer {token}'},
#     )
#     assert response.status_code == HTTPStatus.OK
#     assert response.json()['title'] == 'teste!'
#
#
# @pytest.mark.asyncio
# async def test_delete_todo(session, client, user, token):
#     todo = TodoFactory(user_id=user.id)
#
#     session.add(todo)
#     await session.commit()
#
#     response = client.delete(
#         f'/todos/{todo.id}', headers={'Authorization': f'Bearer {token}'}
#     )
#
#     assert response.status_code == HTTPStatus.OK
#     assert response.json() == {
#       'message': 'Task has been deleted successfully'
#     }
#
#
# def test_delete_todo_inexistente_deve_retornar_404(client, token):
#     response = client.delete(
#         f'/todos/{10}', headers={'Authorization': f'Bearer {token}'}
#     )
#
#     assert response.status_code == HTTPStatus.NOT_FOUND
#     assert response.json() == {'detail': 'Todo not found'}
#
#
# # @pytest.mark.asyncio
# # async def test_create_todo_error(session, user: User):
# #     todo = Todo(
# #         title='Test Todo',
# #         description='Test Desc',
# #         state='test',
# #         user_id=user.id,
# #     )
# #
# #     session.add(todo)
# #     await session.commit()
# #
# #     with pytest.raises(LookupError):
# #         await session.scalar(select(Todo))
#
#
# def test_list_todos_filter_min_length_exercicio_06(client, token):
#     tiny_string = 'a'
#     response = client.get(
#         f'/todos/?title={tiny_string}',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
#
#
# def test_list_todos_filter_max_length_exercicio_06(client, token):
#     large_string = 'a' * 22
#     response = client.get(
#         f'/todos/?title={large_string}',
#         headers={'Authorization': f'Bearer {token}'},
#     )
#
#     assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
