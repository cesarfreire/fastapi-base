import asyncio
import sys
from http import HTTPStatus
from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_base.database import create_tables
from fastapi_base.routers import auth, group, permission, role, users
from fastapi_base.schemas.response import Response

if sys.platform == 'win32':  # pragma: no cover
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

origins = [
    'http://localhost',
    'http://localhost:8080',
]
app = FastAPI(
    title='FastAPI do Zero',
    description='Aplicação do curso de FastAPI do Zero',
    version='0.1.0',
    contact={'name': 'César Freire', 'email': 'iceesar@live.com'},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

logger = getLogger('uvicorn.error')


@app.on_event('startup')
async def startup_event():  # pragma: no cover
    await create_tables()


app.include_router(users.users_router)
app.include_router(auth.auth_router)
app.include_router(role.roles_router)
app.include_router(permission.permissions_router)
app.include_router(group.groups_router)


@app.get('/status', status_code=HTTPStatus.OK, response_model=Response)
async def read_root():
    return {'message': 'Up!'}
