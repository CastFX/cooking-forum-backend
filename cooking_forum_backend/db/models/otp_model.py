from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped, mapped_column, relationship

from cooking_forum_backend.db.base import Base

class OTPModel(Base):
    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    value: Mapped[int]
    expires_at: Mapped[datetime]
    used_at: Mapped[Optional[datetime]]

    def __repr__(self) -> str:
        return f"OTP(id={self.id!r}, user_id={self.user_id!r}, value={self.value!r}), expires_at={self.expires_at!r}, used_at={self.used_at!r}"
