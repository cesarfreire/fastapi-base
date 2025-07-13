from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_root_deve_retornar_ok(client):
    response = await client.get('/status')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Up!'}
