from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class User(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = Field(False)
    reputation: float = Field(0, nullable=False)
    force: float = Field(0, nullable=False)
    update_reputation_at: Optional[datetime] = None
    discourse_id: Optional[int] = Field(None, unique=True)
    discourse_api_key: Optional[str] = None
    discourse_request_nonce: Optional[str] = None
    discourse_notifications_enabled: bool = Field(False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
