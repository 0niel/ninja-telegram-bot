from __future__ import annotations

import datetime

import sqlalchemy as db
from sqlalchemy import UniqueConstraint

from bot import timezone_offset
from bot.models.base import BaseModel


class MessagesHistory(BaseModel):
    __tablename__ = "messages_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger)
    date = db.Column(db.Date, default=datetime.datetime.now(timezone_offset).date())
    messages = db.Column(db.BigInteger, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "date", name="unique_user_date"),)
