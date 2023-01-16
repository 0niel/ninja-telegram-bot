import datetime

from sqlalchemy import select

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


async def add_message(user_id: int, date: datetime.date):
    """Add message to history. If message already exists, increment messages count"""
    async with session() as db:
        if messages_history := (
            await db.execute(
                select(MessagesHistory).where(
                    MessagesHistory.user_id == user_id,
                    MessagesHistory.date == date,
                )
            )
        ).scalar_one_or_none():
            messages_history.messages += 1
        else:
            messages_history = MessagesHistory(user_id=user_id, messages=1)
            db.add(messages_history)
        await db.commit()
