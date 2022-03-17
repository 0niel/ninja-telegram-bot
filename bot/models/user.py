from __future__ import annotations
import threading
import sqlalchemy as db
from datetime import datetime
from sqlalchemy.sql import expression

from bot.models.db import SESSION, BaseModel, TimedBaseModel


class User(TimedBaseModel):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True, index=True, unique=True)
    username = db.Column(db.UnicodeText)
    first_name = db.Column(db.UnicodeText, nullable=True)
    last_name = db.Column(db.UnicodeText, nullable=True)
    is_admin = db.Column(db.Boolean, server_default=expression.false())
    reputation = db.Column(db.FLOAT,  nullable=False, server_default="0")
    force = db.Column(db.FLOAT,  nullable=False, server_default="0")
    update_reputation_at = db.Column(db.DateTime(True), nullable=True)

    @staticmethod
    def update(user_id, username, first_name, last_name):
        with threading.RLock():
            user = SESSION.query(User).get(user_id)

            if not user:
                user = User(id=user_id, username=username,
                            first_name=first_name, last_name=last_name)
                SESSION.add(user, username)
                SESSION.flush()
            else:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name

            SESSION.commit()

    @staticmethod
    def get(user_id):
        try:
            return SESSION.query(User).get(user_id)
        finally:
            SESSION.close()

    @staticmethod
    def update_rep_and_force(from_user_id, to_user_id, new_rep, new_force):
        with threading.RLock():
            to_user = SESSION.query(User).get(to_user_id)
            from_user = SESSION.query(User).get(from_user_id)
            to_user.reputation = new_rep
            to_user.force = new_force
            from_user.update_reputation_at = db.func.now()
            SESSION.commit()

    def is_rep_change_available(self):
        if self.is_admin:
            return True

        seconds = (
            datetime.now() - self.update_reputation_at.replace(tzinfo=None)).total_seconds()
        minutes = (seconds % 3600) // 60
        return minutes >= 10

    @staticmethod
    def get_by_rating():
        try:
            return SESSION.query(User).select_from(User).order_by(User.reputation.desc()).offset(0).limit(10).all()
        finally:
            SESSION.close()


class UserRelatedModel(BaseModel):
    __abstract__ = True

    user_id = db.Column(
        db.ForeignKey(f"{User.__tablename__}.id",
                      ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )


User.__table__.create(checkfirst=True)
