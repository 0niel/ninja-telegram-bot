from datetime import datetime

from sqlalchemy import select, update

from bot import timezone_offset
from bot.db import session
from bot.models import User


async def update_user_names(user_id: int, username: str, first_name: str, last_name: str):
    async with session() as db:
        if user := (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none():
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        else:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            db.add(user)
        await db.commit()


async def get_by_id(user_id: int) -> User | None:
    async with session() as db:
        res = await db.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()


async def get_by_username(username: str) -> User | None:
    async with session() as db:
        res = await db.execute(select(User).where(User.username == username))
        return res.scalar_one_or_none()


async def update_rep_and_force(from_user_id: int, to_user_id: int, new_rep: float, new_force: float):
    async with session() as db:
        # Update reputation and force of user who received reputation
        await db.execute(update(User).where(User.id == to_user_id).values(reputation=new_rep, force=new_force))

        # Update date of last reputation update of user who sent reputation. It's used to prevent spam of reputation
        # updates
        await db.execute(
            update(User).where(User.id == from_user_id).values(update_reputation_at=datetime.now(timezone_offset))
        )
        await db.commit()


async def update_force(user_id: int, new_force: float):
    """Update force of user"""
    async with session() as db:
        await db.execute(update(User).where(User.id == user_id).values(force=new_force))
        await db.commit()


def is_rep_change_available(user: User, cooldown_seconds: int) -> bool:
    """Check if user can change reputation"""
    second = (datetime.now(timezone_offset) - user.update_reputation_at.replace(tzinfo=timezone_offset)).total_seconds()

    return second >= cooldown_seconds


async def get_top_by_reputation(limit: int):
    """Get top users by reputation"""
    async with session() as db:
        return (await db.execute(select(User).order_by(User.reputation.desc()).limit(limit))).scalars().all()


async def get_rating_slice(user_id, before_count: int, after_count: int) -> list[User]:
    """Get slice of users rating. It's used to show user rating in rating command.  For example, if user has 1000
    rating, and before_count=5 and after_count=5, this function will return 10 users (5 before and 5 after user).
    This function also returns user position in rating"""
    async with session() as db:
        users_without_zero_force = (await db.execute(select(User).order_by(User.reputation.desc()))).scalars().all()

        res = []  # type: list[tuple[User, int]] # (user, rank)

        for rank, user in enumerate(users_without_zero_force, start=1):
            if user.id == user_id:
                user_position = rank
            if user_position - before_count <= rank <= user_position + after_count:
                res.append((user, rank))

        return res
