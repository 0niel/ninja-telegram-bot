from __future__ import annotations

from datetime import datetime, timedelta, timezone

import sqlalchemy as db
from sqlalchemy import func
from sqlalchemy.sql import expression

from bot.db import db_session
from bot.models.base import BaseModel, TimedBaseModel

offset = timezone(timedelta(hours=3))


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

    @staticmethod
    def update(user_id, username, first_name, last_name):
        with db_session() as session:
            user = session.query(User).get(user_id)

            if not user:
                user = User(
                    id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                session.add(user, username)
            else:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name

            session.commit()

    @staticmethod
    def get(user_id):
        with db_session() as session:
            return session.query(User).get(user_id)

    @staticmethod
    def get_by_username(username):
        with db_session() as session:
            return session.query(User).filter(User.username == username).first()

    @staticmethod
    def update_rep_and_force(from_user_id, to_user_id, new_rep, new_force):
        with db_session() as session:
            to_user = session.query(User).get(to_user_id)
            from_user = session.query(User).get(from_user_id)
            to_user.reputation = new_rep
            to_user.force = new_force
            from_user.update_reputation_at = datetime.now(offset)
            session.commit()

    @staticmethod
    def update_force(user_id, new_force):
        with db_session() as session:
            user = session.query(User).get(user_id)
            user.force = new_force
            session.commit()

    def is_rep_change_available(self):
        # if self.is_admin:
        #     return True
        seconds = (
            datetime.now(offset) - self.update_reputation_at.replace(tzinfo=offset)
        ).total_seconds()
        minutes = seconds // 60
        return minutes >= 10

    @staticmethod
    def get_by_rating(limit: int):
        with db_session() as session:
            return (
                session.query(User)
                .select_from(User)
                .order_by(User.reputation.desc())
                .offset(0)
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_rating_slice(user_id, before_count: int, after_count: int):
        with db_session() as session:
            user = session.query(User).get(user_id)

            if user:
                query = session.query(
                    User,
                    func.rank().over(order_by=User.reputation.desc()).label("rank"),
                )

                users = query.filter(User.force != 0).all()

                for tmp_user in users:
                    if tmp_user[0].id == user_id:
                        if tmp_user[1] - 1 - before_count >= 0:
                            start = tmp_user[1] - 1 - before_count
                        else:
                            start = 0

                        if tmp_user[1] + after_count < len(users):
                            end = tmp_user[1] + after_count
                        else:
                            end = len(users)

                        return users[start:end]


class UserRelatedModel(BaseModel):
    __abstract__ = True

    user_id = db.Column(
        db.ForeignKey(
            f"{User.__tablename__}.id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )


User.__table__.create(checkfirst=True)
