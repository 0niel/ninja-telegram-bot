from __future__ import annotations

import datetime

import sqlalchemy as db

from bot.db import db_session
from bot.models.base import BaseModel

offset = datetime.timezone(datetime.timedelta(hours=3))


class MessagesHistory(BaseModel):
    __tablename__ = "messages_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger)
    date = db.Column(db.Date, default=datetime.datetime.now(offset).date())
    messages = db.Column(db.BigInteger, nullable=True)

    @staticmethod
    def add_message(user_id, date):
        with db_session() as session:
            messages_history = (
                session.query(MessagesHistory)
                .filter(
                    MessagesHistory.user_id == user_id, MessagesHistory.date == date
                )
                .first()
            )
            if not messages_history:
                new_messages_history = MessagesHistory(
                    user_id=user_id, date=date, messages=1
                )
                session.add(new_messages_history)
            else:
                messages_history.messages = messages_history.messages + 1

            session.commit()

    @staticmethod
    def get(date):
        with db_session() as db:
            return (
                db.query(MessagesHistory)
                .filter(MessagesHistory.date == date)
                .order_by(MessagesHistory.messages.desc())
                .offset(0)
                .limit(5)
                .all()
            )


MessagesHistory.__table__.create(checkfirst=True)
