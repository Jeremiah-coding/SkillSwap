import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    full_name: str
    bio: Optional[str] = None
    city: Optional[str] = None
    can_teach: Optional[str] = None
    wants_to_learn: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    can_teach: Optional[str] = None
    wants_to_learn: Optional[str] = None
    is_active: Optional[bool] = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    bio: Optional[str]
    city: Optional[str]
    can_teach: Optional[str]
    wants_to_learn: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
