import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    profile_id: uuid.UUID
    message: str
    type: str


class NotificationResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    message: str
    type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
