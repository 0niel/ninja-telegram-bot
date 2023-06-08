import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class MessagesHistory(BaseModel):
    id: int
    tg_user_id: int
    date: datetime.date = Field(default_factory=datetime.date.today)
    messages: Optional[int]
