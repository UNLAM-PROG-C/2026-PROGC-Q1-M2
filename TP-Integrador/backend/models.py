from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

USERNAME_MIN_LENGTH = 1
PASSWORD_MIN_LENGTH = 1
USERNAME_MAX_LENGTH = 50
PASSWORD_MAX_LENGTH = 128


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH
    )
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ReserveSeatsRequest(BaseModel):
    seat_ids: List[int]
    concert_id: int


class ReleaseSeatsRequest(BaseModel):
    seat_ids: List[int]
    concert_id: int


class PaymentRequest(BaseModel):
    seat_ids: List[int]
    concert_id: int
    payment_method: str = "credit_card"
    card_last_four: Optional[str] = "0000"
