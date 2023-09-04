from datetime import datetime, timedelta
import random
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from cooking_forum_backend.db.models.user_model import UserModel
from cooking_forum_backend.db.repositories.otp_repository import OTPRepository

from cooking_forum_backend.db.repositories.user_repository import UserRepository
from cooking_forum_backend.services.crypto import CryptoService
from cooking_forum_backend.services.email_service import EmailService
from cooking_forum_backend.web.api.auth.schema import (
    OtpCheckDTO,
    OtpDTO,
    OtpRequestDTO,
    TokenDTO,
    TokenRequestDTO,
    UserDTO,
    UserInputDTO,
)

router = APIRouter()

async def get_user_by_credentials(
    username: str,
    password: str,
    with_2fa_requested: bool,
    user_repository: UserRepository,
):
    user = await user_repository.authenticate(
        username,
        password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if with_2fa_requested and not user.two_fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Two-factor authentication is not enabled",
            headers={"WWW-Authenticate": 'authType="2FA"'},
        )

    if not with_2fa_requested and user.two_fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Two-factor authentication is required",
            headers={"WWW-Authenticate": 'authType="2FA"'},
        )

    return user



async def get_current_user(
    token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="/api/token"))],
    crypto_service: Annotated[CryptoService, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = crypto_service.decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        user = await user_repository.get_by_username(username)
    except JWTError:
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
    return user


@router.post(
    "/register",
    summary="Register a new user into the forum",
    response_model=UserDTO
)
async def register_user(
    new_user: UserInputDTO,
    user_repository: Annotated[UserRepository, Depends()],
):
    """
    Creates user model in the database.

    :param new_user: new user model item.
    :param user_repository: DAO for user models.
    """
    user = await user_repository.create_user_model(
        username=new_user.username,
        email=new_user.email,
        password=new_user.password,
        two_fa_enabled=new_user.two_fa_enabled,
    )

    return UserDTO.model_validate(user)


@router.post(
    "/token",
    summary="OAuth2 login, password flow. If user has 2FA enabled, it will respond 401: use /token/otp/send",
    response_description="A JWT access token if successful, 401 otherwise",
    response_model=TokenDTO,
)
async def login(
    credentials: Annotated[TokenRequestDTO, Depends()],
    crypto_service: Annotated[CryptoService, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    user = await get_user_by_credentials(
        username=credentials.username,
        password=credentials.password,
        with_2fa_requested=False,
        user_repository=user_repository,
    )
    access_token = crypto_service.create_access_token({"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}



@router.post(
    "/token/otp/send",
    summary="OAuth2 login, password flow, OTP request. It sends an otp to the user's email.",
    response_description="Returns the otp_id that needs to be used in /token/otp/check",
    response_model=OtpDTO
)
async def send_otp(
    credentials: Annotated[OtpRequestDTO, Depends()],
    otp_repository: Annotated[OTPRepository, Depends()],
    email_service: Annotated[EmailService, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    user = await get_user_by_credentials(
        username=credentials.username,
        password=credentials.password,
        with_2fa_requested=True,
        user_repository=user_repository,
    )

    otp = await otp_repository.create_otp(
        user_id=user.id,
        value=random.randint(100000, 999999),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )

    await email_service.sendEmail(user.email, f"Your 2FA code is {otp.value}")

    return {"otp_id": otp.id, "otp_type": "email"}

@router.post(
    "/token/otp/check",
    summary="OAuth2 login, password flow, OTP check. It verifies the otp_value sent to the user, along with the otp_id obtained in /token/otp/send.",
    response_description="A JWT access token if successful, 401 otherwise",
    response_model=TokenDTO
)
async def login_with_otp(
    credentials: Annotated[OtpCheckDTO, Depends()],
    crypto_service: Annotated[CryptoService, Depends()],
    otp_repository: Annotated[OTPRepository, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    user = await get_user_by_credentials(
        username=credentials.username,
        password=credentials.password,
        with_2fa_requested=True,
        user_repository=user_repository,
    )

    otp = await otp_repository.get_active_by_user_id(user.id)

    if not otp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP Not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    
    if otp.id != credentials.otp_id or otp.value != credentials.otp_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = crypto_service.create_access_token({"sub": user.username})

    await otp_repository.set_used_at(otp.id)

    return {"access_token": access_token, "token_type": "bearer"}

@router.get(
    "/users/me",
    summary="Get current logged user",
    response_model=UserDTO
)
async def me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    return UserDTO.model_validate(current_user)


@router.get(
    "/users/",
    summary="Get all users, does not require authentication",
    response_model=List[UserDTO]
)
async def get_users(
    user_repository: Annotated[UserRepository, Depends()],
    limit: int = 10,
    offset: int = 0,
) -> List[UserModel]:
    """
    Retrieve all users objects from the database.

    :param limit: limit of users objects, defaults to 10.
    :param offset: offset of users objects, defaults to 0.
    :param users_dao: DAO for users models.
    :return: list of users objects from database.
    """
    return await user_repository.get_all_users(limit=limit, offset=offset)
