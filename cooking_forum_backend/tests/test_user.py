import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from cooking_forum_backend.db.repositories.user_repository import UserRepository


@pytest.mark.anyio
async def test_creation(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests user instance creation."""
    url = fastapi_app.url_path_for("register_user")
    test_name = uuid.uuid4().hex
    test_email = uuid.uuid4().hex + "@email.com"
    test_password = uuid.uuid4().hex
    response = await client.post(
        url,
        json={
            "username": test_name,
            "email": test_email,
            "password": test_password,
            "two_fa_enabled": False,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    repository = UserRepository(dbsession)
    user = await repository.get_by_username(test_name)
    assert user.username == test_name
    assert user.email == test_email
    assert user.password != test_password
    assert user.two_fa_enabled == False

