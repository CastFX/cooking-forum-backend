from datetime import datetime
from typing import Annotated
from attr import dataclass

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

class TokenRequestDTO(BaseModel):
    username: str
    password: str

class OtpRequestDTO(TokenRequestDTO):
    pass

class OtpChecktDTO(TokenRequestDTO):
    otp_id: int
    otp_value: int
