from datetime import datetime
from typing import List, Optional, Union

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cooking_forum_backend.db.dependencies import get_db_session
from cooking_forum_backend.db.models.user_model import UserModel
from cooking_forum_backend.services.crypto import CryptoService


class UserRepository:
    """Class for accessing users table."""

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
    ) -> UserModel:
        user = UserModel(
            username=username,
            email=email,
            password=self.crypto_service.hash_password(password),
            two_fa_enabled=two_fa_enabled,
            created_at=created_at or datetime.utcnow(),
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def get_by_username(self, username) -> UserModel:
        results = await self.session.execute(
            select(UserModel).where(UserModel.username == username),
        )
        return results.scalar_one()
    
    async def get_all_users(self, limit: int, offset: int) -> List[UserModel]:
        """
        Get all user models with limit/offset pagination.

        :param limit: limit of users.
        :param offset: offset of users.
        :return: stream of users.
        """
        raw_users = await self.session.execute(
            select(UserModel).limit(limit).offset(offset),
        )

        return list(raw_users.scalars().fetchall())

    async def authenticate(self, username: str, password: str) -> Union[bool, UserModel]:
        user = await self.get_by_username(username)
        if not user:
            return False

        if not self.crypto_service.check_password(password, user.password):
            return False

        return user
