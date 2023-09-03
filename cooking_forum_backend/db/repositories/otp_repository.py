from datetime import datetime
from typing import Optional
from certifi import where

from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from cooking_forum_backend.db.dependencies import get_db_session
from cooking_forum_backend.db.models.otp_model import OTPModel

class OTPRepository:
    """Class for accessing otps table."""

    def __init__(
        self,
        session: AsyncSession = Depends(get_db_session),
    ):
        self.session = session

    async def create_otp(
        self,
        user_id: int,
        value: str,
        expires_at: datetime,
    ) -> OTPModel:
        otp = OTPModel(
            user_id=user_id,
            value=value,
            expires_at=expires_at,
        )
        self.session.add(otp)
        await self.session.commit()
        await self.session.refresh(otp)

        return otp
    
    async def get_active_by_user_id(self, user_id: int) -> OTPModel:
        results = await self.session.execute(
            select(OTPModel)
                .where(OTPModel.user_id == user_id)
                .where(OTPModel.expires_at > datetime.utcnow())
                .where(OTPModel.used_at is None)
                .order_by(OTPModel.expires_at.desc())
        )

        return results.scalar_one()
    
    async def set_used_at(self, otp_id: int, used_at: Optional[datetime]) -> OTPModel:
        return await self.session.execute(
            update(OTPModel)
                .values(used_at=used_at or datetime.now())
                .where(OTPModel.id == otp_id)
        )