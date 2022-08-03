from __future__ import annotations

import datetime

import sqlalchemy as db

from bot.db import db_session
from bot.models.base import BaseModel

offset = datetime.timezone(datetime.timedelta(hours=3))


class UserScript(BaseModel):
    __tablename__ = "user_scripts"

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.BigInteger)
    created_at = db.Column(db.Date, default=datetime.datetime.now(offset).date())
    name = db.Column(db.UnicodeText, nullable=False, index=True, unique=True)
    script = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)

    @staticmethod
    def create(author_id, name, script, description):
        with db_session() as session:
            new_user_script = UserScript(
                author_id=author_id, name=name, script=script, description=description
            )
            session.add(new_user_script)
            session.commit()

    @staticmethod
    def get_by_name(name):
        with db_session() as session:
            return (
                session.query(UserScript)
                .filter(
                    UserScript.name == name,
                )
                .first()
            )

    @staticmethod
    def get_by_author(author_id):
        with db_session() as session:
            return (
                session.query(UserScript)
                .filter(
                    UserScript.author_id == author_id,
                )
                .all()
            )

    @staticmethod
    def get_all():
        with db_session() as session:
            return (
                session.query(UserScript)
                .select_from(UserScript)
                .order_by(UserScript.created_at.desc())
                .offset(0)
                .all()
            )

    @staticmethod
    def rename(old_name, new_name):
        with db_session() as session:
            script = (
                session.query(UserScript).filter(UserScript.name == old_name).first()
            )
            script.name = new_name
            session.commit()

    @staticmethod
    def change_desc(name, new_desc):
        with db_session() as session:
            script = session.query(UserScript).filter(UserScript.name == name).first()
            script.description = new_desc
            session.commit()

    @staticmethod
    def delete_by_name(name):
        with db_session() as session:
            script = session.query(UserScript).filter(UserScript.name == name).first()
            session.delete(script)
            session.commit()


UserScript.__table__.create(checkfirst=True)
