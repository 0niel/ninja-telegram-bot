from __future__ import annotations

import datetime

import sqlalchemy as db

from bot.models.base import BaseModel

offset = datetime.timezone(datetime.timedelta(hours=3))


class MessagesHistory(BaseModel):
    __tablename__ = "messages_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger)
    date = db.Column(db.Date, default=datetime.datetime.now(offset).date())
    messages = db.Column(db.BigInteger, nullable=True)
