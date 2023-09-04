import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from cooking_forum_backend.db.repositories.user_repository import UserRepository
from cooking_forum_backend.services.crypto import CryptoService

@pytest.mark.anyio
async def test_authenticated_user_can_get_self(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests successful authentication of user."""
    crypto_service = CryptoService()
    repository = UserRepository(dbsession, crypto_service)

    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    user = await repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=False,
    )

    token_response = await client.post(
        fastapi_app.url_path_for("login"),
        data={ 
            "username": test_name,
            "password": test_password,
        },
    )
    assert token_response.status_code == status.HTTP_200_OK
    data = token_response.json()
    
    auth_header = "Bearer " + data["access_token"]

    me_response = await client.get(
        fastapi_app.url_path_for("me"),
        headers={
            "Authorization": auth_header
        }
    )

    assert me_response.status_code == status.HTTP_200_OK
    data = me_response.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email

@pytest.mark.anyio
async def test_unauthenticated_user_cannot_get_self(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests missing authentication of user."""
    crypto_service = CryptoService()
    repository = UserRepository(dbsession, crypto_service)

    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    await repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=False,
    )

    me_response = await client.get(
        fastapi_app.url_path_for("me"),
        headers={
            "Authorization": "None"
        }
    )

    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED


