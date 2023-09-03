from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Boolean, DateTime, String

from cooking_forum_backend.db.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(length=200))  # noqa: WPS432
    email: Mapped[str] = mapped_column(String(length=320))
    password: Mapped[str] = mapped_column(String(length=255))
    two_fa_enabled: Mapped[bool] = mapped_column(Boolean())
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r}), 2fa={self.two_fa_enabled!r}, created_at={self.created_at!r}"
