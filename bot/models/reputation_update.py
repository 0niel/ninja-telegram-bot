from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReputationUpdate(BaseModel):
    id: int | None = None
    from_tg_user_id: int
    to_tg_user_id: Optional[int] = None
    message_id: Optional[int] = None
    reputation_delta: Optional[float] = None
    force_delta: Optional[float] = None
    new_reputation: float
    new_force: float
    updated_at: datetime = Field(default_factory=datetime.now)
