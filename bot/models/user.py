from __future__ import annotations

import sqlalchemy as db
from sqlalchemy.sql import expression

from bot.models.base import BaseModel, TimedBaseModel


class User(TimedBaseModel):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, index=True, unique=True)
    username = db.Column(db.UnicodeText)
    first_name = db.Column(db.UnicodeText, nullable=True)
    last_name = db.Column(db.UnicodeText, nullable=True)
    is_admin = db.Column(db.Boolean, server_default=expression.false())
    reputation = db.Column(db.FLOAT, nullable=False, server_default="0")
    force = db.Column(db.FLOAT, nullable=False, server_default="0")
    update_reputation_at = db.Column(db.DateTime(True), nullable=True)


class UserRelatedModel(BaseModel):
    __abstract__ = True

    user_id = db.Column(
        db.ForeignKey(f"{User.__tablename__}.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
