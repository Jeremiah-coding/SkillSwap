import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionCreate(BaseModel):
    requester_profile_id: uuid.UUID
    mentor_profile_id: uuid.UUID
    requested_skill: str
    message: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class SessionStatusUpdate(BaseModel):
    status: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    requester_profile_id: uuid.UUID
    mentor_profile_id: uuid.UUID
    requested_skill: str
    message: Optional[str]
    scheduled_date: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
