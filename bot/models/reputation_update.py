from __future__ import annotations

import datetime

import sqlalchemy as db

from bot import timezone_offset
from bot.models.base import BaseModel


class ReputationUpdate(BaseModel):
    __tablename__ = "reputation_updates"

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.BigInteger)
    to_user_id = db.Column(db.BigInteger, nullable=True)
    message_id = db.Column(db.BigInteger, nullable=True)
    reputation_delta = db.Column(db.FLOAT, nullable=True)
    force_delta = db.Column(db.FLOAT, nullable=True)
    new_reputation = db.Column(db.FLOAT)
    new_force = db.Column(db.FLOAT)
    updated_at = db.Column(db.DateTime(True), default=datetime.datetime.now(timezone_offset))
