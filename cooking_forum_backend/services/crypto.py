from datetime import datetime, timedelta
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from cooking_forum_backend.settings import settings


class CryptoService:
    """Class for accessing user table."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = settings.jwt_algorithm
        self.jwt_expires_delta = timedelta(minutes=settings.jwt_expires_minutes)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def check_password(self, password: str, hashed_password: str):
        return self.pwd_context.verify(
            password,
            hashed_password,
        )

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or self.jwt_expires_delta)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            key=self.jwt_secret,
            algorithm=self.jwt_algorithm,
        )
        return encoded_jwt

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            token,
            key=self.jwt_secret,
            algorithms=[self.jwt_algorithm],
        )
