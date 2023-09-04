import datetime
import random
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from cooking_forum_backend.db.models.user_model import UserModel
from cooking_forum_backend.db.repositories.otp_repository import OTPRepository

from cooking_forum_backend.db.repositories.user_repository import UserRepository
from cooking_forum_backend.services.crypto import CryptoService
from cooking_forum_backend.services.email_service import EmailService
from cooking_forum_backend.web.api.auth.schema import (
    ChallengeDTO,
    TokenDTO,
    UserDTO,
    UserInputDTO,
)

router = APIRouter()


async def get_user_by_credentials(
    form_data: OAuth2PasswordRequestForm,
    with_2fa_requested: bool,
    user_repository: UserRepository,
):
    user = await user_repository.authenticate(
        form_data.username,
        form_data.password,
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
    token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="token"))],
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


@router.post("/register", response_model=UserDTO)
async def register_user(
    new_user_object: UserInputDTO,
    user_repository: Annotated[UserRepository, Depends()],
):
    """
    Creates user model in the database.

    :param new_user_object: new user model item.
    :param user_repository: DAO for user models.
    """
    user = await user_repository.create_user_model(
        username=new_user_object.username,
        email=new_user_object.email,
        password=new_user_object.password,
        two_fa_enabled=new_user_object.two_fa_enabled,
    )

    return UserDTO.model_validate(user)


@router.post("/token", response_model=TokenDTO)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    crypto_service: Annotated[CryptoService, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    user = await get_user_by_credentials(
        form_data=form_data,
        with_2fa_requested=False,
        user_repository=user_repository,
    )
    access_token = crypto_service.create_access_token({"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/challenge/create", response_model=ChallengeDTO)
async def create_challenge(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    otp_repository: Annotated[OTPRepository, Depends()],
    email_service: Annotated[EmailService, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    user = await get_user_by_credentials(
        form_data=form_data,
        with_2fa_requested=True,
        user_repository=user_repository,
    )

    otp = await otp_repository.create_otp(
        user_id=user.id,
        value=random.randint(100000, 999999),
        expires_at=datetime.utcnow() + datetime.timedelta(minutes=15),
    )

    await email_service.sendEmail(user.email, f"Your 2FA code is {otp.value}")

    return {"challenge_id": otp.id, "type": "email"}

@router.post("/challenge/verify", response_model=TokenDTO)
async def login_with_2fa_challenge(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    crypto_service: Annotated[CryptoService, Depends()],
    otp_repository: Annotated[OTPRepository, Depends()],
    user_repository: Annotated[UserRepository, Depends()],
):
    user = await get_user_by_credentials(
        form_data=form_data,
        with_2fa_requested=True,
        user_repository=user_repository,
    )

    otp = await otp_repository.get_active_by_user_id(user.id)

    if not otp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid otp id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = crypto_service.create_access_token({"sub": user.username})

    await otp_repository.set_used_at(otp.id)

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserDTO)
async def me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    return UserDTO.model_validate(current_user)


@router.get("/users/", response_model=List[UserDTO])
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
