from sqlalchemy import select

from bot.db import session
from bot.models import ReputationUpdate


async def create(reputation_update: ReputationUpdate) -> None:
    """Create reputation update"""
    async with session() as db:
        db.add(reputation_update)
        await db.commit()


async def get_by_user_id(user_id: int, limit=10, offset=0) -> list[ReputationUpdate]:
    """Get user reputation history"""
    async with session() as db:
        return await db.execute(
            select(ReputationUpdate)
            .where(ReputationUpdate.to_user_id == user_id)
            .order_by(ReputationUpdate.updated_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()


async def is_user_send_rep_to_message(user_id: int, message_id: int) -> bool:
    """Check if user send reputation to message"""
    async with session() as db:
        result = await db.execute(
            select(ReputationUpdate).where(
                ReputationUpdate.from_user_id == user_id,
                ReputationUpdate.message_id == message_id,
            )
        ).first()
        return bool(result)
