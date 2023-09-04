from datetime import datetime
from typing import Annotated
from attr import dataclass
from fastapi import Form

from pydantic import BaseModel, ConfigDict


class UserDTO(BaseModel):
    """
    DTO for user models.

    It returned when accessing user models from the API.
    """

    id: int
    username: str
    email: str
    two_fa_enabled: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserInputDTO(BaseModel):
    """
    DTO to create user models from input.
    """

    username: str
    email: str
    password: str
    two_fa_enabled: bool


class OtpDTO(BaseModel):
    """
    DTO for 2FA challenges.
    """

    otp_id: int
    otp_type: str


class TokenDTO(BaseModel):
    """
    DTO for JWT like auth tokens
    """

    access_token: str
    token_type: str

# class TokenRequestDTO(BaseModel):
#     username: str = Form(...)
#     password: str = Form(...)


# class OtpCheckDTO(TokenRequestDTO):
#     otp_id: int = Form(...)
#     otp_value: int = Form(...)

class TokenRequestDTO:
    def __init__(
        self,
        *,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ):
        self.username = username
        self.password = password

class OtpRequestDTO(TokenRequestDTO):
    pass
class OtpCheckDTO:
    def __init__(
        self,
        *,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        otp_id: Annotated[int, Form()],
        otp_value: Annotated[int, Form()],
    ):
        self.username = username
        self.password = password
        self.otp_id = otp_id
        self.otp_value = otp_value