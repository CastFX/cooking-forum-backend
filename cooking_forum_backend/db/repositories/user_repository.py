from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cooking_forum_backend.db.dependencies import get_db_session
from cooking_forum_backend.db.models.user_model import UserModel
from cooking_forum_backend.services.crypto import CryptoService


class UserRepository:
    """Class for accessing user table."""

    def __init__(
        self,
        session: AsyncSession = Depends(get_db_session),
        crypto_service: CryptoService = Depends(),
    ):
        self.session = session
        self.crypto_service = crypto_service

    async def create_user_model(
        self,
        username: str,
        email: str,
        password: str,
        two_fa_enabled: bool,
        created_at: Optional[datetime] = None,
    ) -> None:
        self.session.add(
            UserModel(
                username=username,
                email=email,
                password=self.crypto_service.hash_password(password),
                two_fa_enabled=two_fa_enabled,
                created_at=created_at or datetime.utcnow(),
            ),
        )

    async def get_by_email(self, email) -> UserModel:
        return await self.session.execute(
            select(UserModel).where(UserModel.email == email),
        ).scalar_one()

    async def authenticate(self, email: str, password: str) -> False | UserModel:
        user = await self.get_by_email(email)
        if not user:
            return False

        if not self.crypto_service.check_password(password, user.password):
            return False

        return user
