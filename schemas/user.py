from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class SubscriptionDTO(BaseModel):
    ticker: str
    user_id: int
    chat_id: str

    model_config = ConfigDict(from_attributes=True)


class UserDTO(BaseModel):
    id: int
    provider: str
    provider_id: str
    is_authorized: bool
    created_at: datetime

    subscriptions: List[SubscriptionDTO] = []

    model_config = ConfigDict(from_attributes=True)
