from passlib.context import CryptContext


class CryptoService:
    """Class for accessing user table."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def check_password(self, password: str, hashed_password: str):
        return self.pwd_context.verify(
            password,
            hashed_password,
        )
