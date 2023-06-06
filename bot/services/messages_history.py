import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from bot.db import session
from bot.models import MessagesHistory


async def get_by_user_id(user_id: int, limit: int = 5, offset: int = 0):
    """Get user messages history"""
    async with session() as db:
        return (
            (
                await db.execute(
                    select(MessagesHistory)
                    .where(MessagesHistory.user_id == user_id)
                    .order_by(MessagesHistory.date.desc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )


async def get_top_by_date(date: datetime.date, limit: int = 5):
    """Get top users by messages count"""
    async with session() as db:
        return (
            (
                await db.execute(
                    select(MessagesHistory)
                    .where(MessagesHistory.date == date)
                    .order_by(MessagesHistory.messages.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )


async def add_message(user_id: int, date: datetime.date):
    """Add message to history. If message already exists, increment messages count"""
    async with session() as db:
        stmt = pg_insert(MessagesHistory).values(user_id=user_id, date=date, messages=1)
        stmt = stmt.on_conflict_do_update(
            index_elements=[MessagesHistory.user_id, MessagesHistory.date],
            set_=dict(messages=MessagesHistory.messages + 1),
        )
        await db.execute(stmt)
        await db.commit()
