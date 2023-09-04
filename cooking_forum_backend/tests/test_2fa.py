import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from cooking_forum_backend.db.models.otp_model import OTPModel
from cooking_forum_backend.db.repositories.otp_repository import OTPRepository

from cooking_forum_backend.db.repositories.user_repository import UserRepository
from cooking_forum_backend.services.crypto import CryptoService



@pytest.mark.anyio
async def test_otp_send_without_2FA_enabled(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests 2fa login with OTP fails without 2FA enabled."""
    repository = UserRepository(dbsession, CryptoService())
    

    url = fastapi_app.url_path_for("send_otp")
    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    await repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=False,
    )

    response = await client.post(
        url,
        json={
            "username": test_name,
            "password": test_password,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
async def test_otp_send_with_2FA(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests 2fa login with OTP for email."""
    user_repository = UserRepository(dbsession, CryptoService())
    otp_repository = OTPRepository(dbsession)
    
    url = fastapi_app.url_path_for("send_otp")
    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    user = await user_repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=True,
    )
    response = await client.post(
        url,
        json={
            "username": test_name,
            "password": test_password,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["otp_type"] == "email"
    otp_id = data["otp_id"]

    otp = await otp_repository.get_active_by_user_id(user.id)
    assert otp.id == otp_id


@pytest.mark.anyio
async def test_otp_check_successful(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests 2fa login with OTP for email."""
    user_repository = UserRepository(dbsession, CryptoService())
    otp_repository = OTPRepository(dbsession)
    
    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    user = await user_repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=True,
    )
    send_response = await client.post(
        fastapi_app.url_path_for("send_otp"),
        json={
            "username": test_name,
            "password": test_password,
        },
    )
    assert send_response.status_code == status.HTTP_200_OK
    data = send_response.json()

    otp = await otp_repository.get_active_by_user_id(user.id)

    verify_response = await client.post(
        fastapi_app.url_path_for("login_with_otp"),
        json={
            "username": test_name,
            "password": test_password,
            "opt_id": data['otp_id'],
            "otp_value": otp.value
        },
    )

    assert verify_response.status_code == status.HTTP_200_OK
    data = verify_response.json()
    assert data["token_type"] == "bearer"
    jwt = CryptoService().decode_access_token(data["access_token"])
    assert jwt["sub"] == test_name

@pytest.mark.anyio
async def test_otp_check_failure(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests 2fa login with OTP for email."""
    user_repository = UserRepository(dbsession, CryptoService())
    otp_repository = OTPRepository(dbsession)
    
    test_name = uuid.uuid4().hex
    test_password = uuid.uuid4().hex

    user = await user_repository.create_user_model(
        username=test_name,
        email=test_name + "@email.com",
        password=test_password,
        two_fa_enabled=True,
    )
    send_response = await client.post(
        fastapi_app.url_path_for("send_otp"),
        json={
            "username": test_name,
            "password": test_password,
        },
    )
    assert send_response.status_code == status.HTTP_200_OK
    data = send_response.json()

    otp = await otp_repository.get_active_by_user_id(user.id)

    verify_response = await client.post(
        fastapi_app.url_path_for("login_with_otp"),
        json={
            "username": test_name,
            "password": test_password,
            "opt_id": data['otp_id'] + 1, #wrong otp_id
            "otp_value": otp.value
        },
    )

    assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED

    verify_response = await client.post(
        fastapi_app.url_path_for("login_with_otp"),
        json={
            "username": test_name,
            "password": test_password,
            "opt_id": data['otp_id'],
            "otp_value": otp.value + 1 #wrong otp_value
        },
    )

    assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED






