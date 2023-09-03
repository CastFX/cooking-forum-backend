from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordRequestForm

from cooking_forum_backend.db.repositories.user_repository import UserRepository
from cooking_forum_backend.services.crypto import CryptoService
from cooking_forum_backend.web.api.auth.schema import (
    ChallengeDTO,
    TokenDTO,
    UserDTO,
    UserInputDTO,
)

router = APIRouter()


@router.post("/register")
async def register_user(
    new_user_object: UserInputDTO,
    user_repository: Annotated[UserRepository, Depends()],
):
    """
    Creates user model in the database.

    :param new_user_object: new user model item.
    :param user_repository: DAO for user models.
    """
    await user_repository.create_user_model(
        username=new_user_object.username,
        email=new_user_object.email,
        password=new_user_object.password,
        two_fa_enabled=new_user_object.two_fa_enabled,
    )


@router.post("/login", response_model=TokenDTO)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    crypto_service: Annotated[CryptoService, Depends()],
):
    user = await get_user_by_credentials(
        form_data=form_data,
        with_2fa_requested=False,
    )
    # TODO: return JWT


@router.post("/challenge/create", response_model=ChallengeDTO)
async def create_challenge(
    form_data: OAuth2PasswordRequestForm = Depends(),
    crypto_service: CryptoService = Depends(),
):
    user = get_user_by_credentials(
        form_data=form_data,
        with_2fa_requested=True,
    )

    # TODO: create challenge and send it


@router.post("challenge/verify")
async def login_with_2fa_challenge(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await get_user_by_credentials(
        form_data=form_data,
        with_2fa_requested=True,
    )

    # TODO login if challenge is valid


@router.get("/me", response_model=UserDTO)
async def me(
    current_user,
):
    pass


async def get_user_by_credentials(
    form_data: OAuth2PasswordRequestForm,
    with_2fa_requested: bool,
    user_repository: UserRepository = Depends(),
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
