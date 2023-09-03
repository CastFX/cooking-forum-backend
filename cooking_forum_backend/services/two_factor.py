import random

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from cooking_forum_backend.db.models.user_model import UserModel
from cooking_forum_backend.services.email_service import EmailService


class LoginWithTwoFactorDTO(OAuth2PasswordRequestForm):
    challenge_response: str


class TwoFactorService:
    def __init__(self, email_service: EmailService = Depends()):
        self.email_service = email_service

    async def send_otp(
        self,
        user: UserModel,
    ):
        code = str(random.randint(100000, 999999))
        content = f"Your 2FA code is {code}"

        self.email_service.sendEmail(email=user.email, content=content)
