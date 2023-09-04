import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from cooking_forum_backend.db.repositories import user_repository

from cooking_forum_backend.db.repositories.user_repository import UserRepository
from cooking_forum_backend.services.crypto import CryptoService



@pytest.mark.anyio
async def test_login_fails_with_2FA(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests user instance creation."""
    repository = UserRepository(dbsession, CryptoService())
    

    url = fastapi_app.url_path_for("login")
    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    await repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=True,
    )
    print(url)
    response = await client.post(
        url,
        json={
            "username": test_name,
            "password": test_password,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED





